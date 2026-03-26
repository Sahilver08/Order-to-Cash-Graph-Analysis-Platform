from __future__ import annotations

import json
import os
from typing import Any

import requests

REFUSAL_MESSAGE = "This system is designed to answer questions related to the provided dataset only."
DEFAULT_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"


class HuggingFaceClient:
    def __init__(self, api_token: str | None = None, model: str = DEFAULT_MODEL) -> None:
        self.api_token = api_token or os.getenv("HF_API_TOKEN", "")
        # Temporarily disable HF for reliable rule-based fallback
        self.api_token = ""
        self.model = model
        self.base_url = f"https://api-inference.huggingface.co/models/{self.model}"

    @property
    def is_enabled(self) -> bool:
        return bool(self.api_token)

    def classify_and_extract_template(self, question: str) -> dict[str, Any]:
        if not self.is_enabled:
            return {"ok": False, "error": "HF API token not configured"}

        schema_text = (
            '{"domain_related": true|false, '
            '"template": "top_products_by_billing_count|trace_billing_document_flow|broken_flow_detection|none", '
            '"params": {"top_n"?: number, "billing_document_id"?: string}}'
        )
        prompt = (
            "You are a strict query classification and extraction assistant for an SAP Order-to-Cash (O2C) dataset system.\n\n"

            "Your job:\n"
            "- Determine if the question is related to the dataset\n"
            "- Map it to one of the supported query templates\n"
            "- Extract required parameters\n\n"

            "Supported templates:\n"
            "1. top_products_by_billing_count\n"
            "2. trace_billing_document_flow\n"
            "3. broken_flow_detection\n\n"

            "Examples:\n"
            "Q: Which products have the highest billing count?\n"
            "A: {\"domain_related\": true, \"template\": \"top_products_by_billing_count\", \"params\": {\"top_n\": 5}}\n\n"

            "Q: Show top 3 most billed products\n"
            "A: {\"domain_related\": true, \"template\": \"top_products_by_billing_count\", \"params\": {\"top_n\": 3}}\n\n"

            "Q: Which items are most frequently billed?\n"
            "A: {\"domain_related\": true, \"template\": \"top_products_by_billing_count\", \"params\": {\"top_n\": 5}}\n\n"

            "Q: Trace billing document 90504281\n"
            "A: {\"domain_related\": true, \"template\": \"trace_billing_document_flow\", \"params\": {\"billing_document_id\": \"90504281\"}}\n\n"

            "Q: Show full flow for billing 90504281\n"
            "A: {\"domain_related\": true, \"template\": \"trace_billing_document_flow\", \"params\": {\"billing_document_id\": \"90504281\"}}\n\n"

            "Q: Find broken flows\n"
            "A: {\"domain_related\": true, \"template\": \"broken_flow_detection\", \"params\": {}}\n\n"

            "Q: Show incomplete orders\n"
            "A: {\"domain_related\": true, \"template\": \"broken_flow_detection\", \"params\": {}}\n\n"

            "Q: Who is Virat Kohli?\n"
            "A: {\"domain_related\": false, \"template\": \"none\", \"params\": {}}\n\n"

            "Rules:\n"
            "- Only mark domain_related=false for clearly unrelated questions\n"
            "- Always return valid JSON\n"
            "- Do NOT explain anything\n"
            "- Do NOT add extra text\n\n"

            f"Question: {question}\n"
            "JSON:"
        )

        text = self._generate_text(prompt)
        parsed = _safe_json_extract(text)
        if not isinstance(parsed, dict):
            return {"ok": False, "error": "Could not parse HF JSON response", "raw": text}

        return {"ok": True, "data": parsed}

    def summarize_grounded_answer(
        self, question: str, template: str, params: dict[str, Any], result: dict[str, Any]
    ) -> str:
        if not self.is_enabled:
            return "Query executed on dataset-backed template successfully."

        prompt = (
            "You are a data assistant answering strictly from provided dataset results.\n\n"

            "Rules:\n"
            "- Only use the given result data\n"
            "- Do NOT hallucinate\n"
            "- If result is empty, clearly say no matching records found\n"
            "- Keep the answer concise and structured\n\n"

            "Formatting guidelines:\n"
            "- Use numbered or bullet format when listing items\n"
            "- Clearly label entities like Sales Order, Delivery, Billing, Payment\n"
            "- Keep response clean and user-friendly\n\n"

            f"Question: {question}\n"
            f"Template: {template}\n"
            f"Params: {json.dumps(params)}\n"
            f"Result: {json.dumps(result)}\n\n"
            "Answer:"
        )
        return self._generate_text(prompt).strip() or "Query executed on dataset-backed template successfully."

    def _generate_text(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_token}"}
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 256, "temperature": 0.1, "return_full_text": False},
        }
        try:
            response = requests.post(
                self.base_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return ""

        if isinstance(data, list) and data and isinstance(data[0], dict):
            return str(data[0].get("generated_text", "")).strip()
        if isinstance(data, dict) and "generated_text" in data:
            return str(data.get("generated_text", "")).strip()
        return ""


def _safe_json_extract(text: str) -> Any:
    text = text.strip()
    if not text:
        return None

    # Try as-is first.
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to recover from wrapped text by extracting first JSON object.
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    snippet = text[start: end + 1]
    try:
        return json.loads(snippet)
    except Exception:
        return None
