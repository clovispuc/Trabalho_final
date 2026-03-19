"""Cliente de integracao com a API do Gemini."""

import json
import os
from typing import Any, Dict


class GeminiDecisionError(RuntimeError):
    """Erro de integracao ou validacao na resposta do Gemini."""


class GeminiExpenseDecisionClient:
    """Encapsula a chamada ao Gemini para decisao estruturada em JSON."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def analyze(self, prompt: str) -> Dict[str, Any]:
        if not self.api_key:
            raise GeminiDecisionError("GEMINI_API_KEY nao configurada")

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise GeminiDecisionError("Dependencia google-genai nao instalada") from exc

        schema = {
            "type": "object",
            "required": [
                "status",
                "reason",
                "response",
                "confidence",
                "needs_manual_review",
                "policy_summary",
                "used_cep_tool",
            ],
            "properties": {
                "status": {
                    "type": "string",
                    "enum": [
                        "APROVADA",
                        "REPROVADA",
                        "REPROVADA - O valor excede o limite estabelecido no Blueprint",
                        "REVISÃO MANUAL",
                    ],
                },
                "reason": {"type": "string"},
                "response": {"type": "string"},
                "confidence": {"type": "number"},
                "needs_manual_review": {"type": "boolean"},
                "policy_summary": {"type": "string"},
                "used_cep_tool": {"type": "boolean"},
            },
        }

        client = genai.Client(api_key=self.api_key)

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_json_schema=schema,
                ),
            )
        except Exception as exc:
            raise GeminiDecisionError(f"Falha ao consultar Gemini: {exc}") from exc

        response_text = getattr(response, "text", "") or ""
        if not response_text.strip():
            raise GeminiDecisionError("Gemini retornou resposta vazia")

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise GeminiDecisionError("Gemini retornou JSON invalido") from exc
