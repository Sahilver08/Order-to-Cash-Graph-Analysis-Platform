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
            "You are an extraction assistant for an SAP O2C dataset system.\n"
            "Rules:\n"
            "- Assume questions about products, billing documents, orders, deliveries, payments are domain-related.\n"
            "- Only set domain_related=false for clearly unrelated topics like weather, jokes, general knowledge.\n"
            "- If question is unrelated, set domain_related=false and template=none.\n"
            "- Output strict JSON only, no prose.\n"
            f"- Use this schema exactly: {schema_text}\n\n"
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
            "You are an assistant answering only from provided execution result.\n"
            "Rules:\n"
            "- Do not add facts not present in result.\n"
            "- If result is empty, say no matching dataset records.\n"
            "- Keep answer concise.\n\n"
            f"Question: {question}\n"
            f"Template: {template}\n"
            f"Params: {json.dumps(params)}\n"
            f"Result: {json.dumps(result)}\n"
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
