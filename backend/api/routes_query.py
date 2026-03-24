from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from backend.graph.query_templates import ALLOWED_TEMPLATES
from backend.llm.hf_client import REFUSAL_MESSAGE

router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    question: str = Field(default="")
    template: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


def _rule_based_template_pick(question: str) -> tuple[str | None, dict[str, Any]]:
    text = question.lower().strip()
    if not text:
        return None, {}

    if (("top" in text) or ("most" in text) or ("highest" in text)) and ("product" in text or "material" in text) and "billing" in text:
        return "top_products_by_billing_count", {"top_n": 5}

    if "trace" in text and "billing" in text and "document" in text:
        tokens = [token for token in text.replace(
            ",", " ").split(" ") if token]
        digits = [token for token in tokens if token.isdigit()]
        if digits:
            return "trace_billing_document_flow", {"billing_document_id": digits[-1]}
        return "trace_billing_document_flow", {}

    if ("broken" in text and "flow" in text) or "delivered" in text or "billed without delivery" in text:
        return "broken_flow_detection", {}

    return None, {}


@router.post("/query")
def query_data(payload: QueryRequest, request: Request) -> dict[str, Any]:
    template_name = payload.template
    params = payload.params or {}
    question_text = payload.question or ""
    hf_client = request.app.state.hf_client

    if not template_name:
        hf_pick = hf_client.classify_and_extract_template(question_text)
        if hf_pick.get("ok"):
            llm_data = hf_pick.get("data", {})
            domain_related = bool(llm_data.get("domain_related"))
            if not domain_related:
                return {"ok": False, "answer": REFUSAL_MESSAGE}

            template_name = llm_data.get("template")
            llm_params = llm_data.get("params")
            if isinstance(llm_params, dict):
                params = llm_params

        # fallback for no token / parsing failure
        if not template_name:
            template_name, picked_params = _rule_based_template_pick(
                question_text)
            if picked_params:
                params = picked_params

    if template_name not in ALLOWED_TEMPLATES:
        return {"ok": False, "answer": REFUSAL_MESSAGE}

    if template_name == "trace_billing_document_flow" and not params.get("billing_document_id"):
        return {"ok": False, "answer": REFUSAL_MESSAGE}

    store = request.app.state.data_store
    template_fn = ALLOWED_TEMPLATES[template_name]
    result = template_fn(store, **params)
    answer_text = hf_client.summarize_grounded_answer(
        question=question_text,
        template=template_name,
        params=params,
        result=result,
    )

    # Fallback human-readable answer with dataset details when LLM returns generic text
    if not answer_text or answer_text.strip().startswith("Query executed on dataset-backed template"):
        if template_name == "top_products_by_billing_count":
            rows = result.get("rows", []) if isinstance(result, dict) else []
            if not rows:
                answer_text = "No billing product records found."
            else:
                lines = ["Top products by billing document count:"]
                for idx, row in enumerate(rows, 1):
                    product_name = row.get("product_name", "")
                    product_id = row.get("product_id", "")
                    billing_count = row.get("billing_count", "")
                    label = f"{product_name} ({product_id})" if product_name else str(
                        product_id)
                    lines.append(f"{idx}. {label}: {billing_count}")
                answer_text = "\n".join(lines)

        elif template_name == "trace_billing_document_flow":
            flow = result.get("flow", []) if isinstance(result, dict) else []
            if not flow:
                answer_text = f"No trace found for billing document {params.get('billing_document_id', '')}."
            else:
                lines = [
                    f"Trace for billing document {params.get('billing_document_id', '')}: "]
                for entry in flow:
                    so = entry.get("sales_orders", "N/A")
                    dl = entry.get("delivery_document", "N/A")
                    mat = entry.get("material", "N/A")
                    lines.append(
                        f"- Sales Order(s): {so}, Delivery: {dl}, Material: {mat}")
                answer_text = "\n".join(lines)

        elif template_name == "broken_flow_detection":
            delivered_not_billed = result.get(
                "delivered_not_billed", []) if isinstance(result, dict) else []
            billed_without_delivery = result.get(
                "billed_without_delivery", []) if isinstance(result, dict) else []
            answer_text = (
                f"Delivered not billed: {len(delivered_not_billed)} records. "
                f"Billed without delivery: {len(billed_without_delivery)} records."
            )

    return {
        "ok": True,
        "template": template_name,
        "params": params,
        "result": result,
        "answer": answer_text,
    }
