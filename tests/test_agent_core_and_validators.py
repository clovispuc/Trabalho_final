import unittest
from pathlib import Path

from src.agent_core import AgentCore
from src.validators import mascarar_dados_sensiveis, sanitizar_despesa_para_llm


class StubGeminiSuccess:
    model = "stub-gemini"

    def is_configured(self):
        return True

    def analyze(self, prompt: str):
        self.last_prompt = prompt
        return {
            "status": "APROVADA",
            "reason": "Valor dentro da politica e sem violacao de regra.",
            "response": "Despesa aprovada conforme politica interna.",
            "confidence": 0.92,
            "needs_manual_review": False,
            "policy_summary": "Alimentacao dentro do limite permitido.",
            "used_cep_tool": False,
        }


class StubGeminiLowConfidence:
    model = "stub-gemini"

    def is_configured(self):
        return True

    def analyze(self, prompt: str):
        return {
            "status": "APROVADA",
            "reason": "Nao tenho contexto suficiente para afirmar a aprovacao com seguranca.",
            "response": "Sugiro analise humana.",
            "confidence": 0.42,
            "needs_manual_review": True,
            "policy_summary": "Contexto insuficiente.",
            "used_cep_tool": False,
        }


class StubGeminiError:
    model = "stub-gemini"

    def is_configured(self):
        return True

    def analyze(self, prompt: str):
        raise RuntimeError("Erro simulado de integracao")


class TestAgentCoreAndValidators(unittest.TestCase):
    def test_mask_sensitive_data_hides_card_and_cpf(self):
        text = "Cartao 4532 1111 2222 3333 e CPF 123.456.789-00"
        masked = mascarar_dados_sensiveis(text)
        self.assertIn("**** **** **** 3333", masked)
        self.assertIn("***.***.***-00", masked)

    def test_sanitize_expense_masks_sensitive_fields_before_prompt(self):
        expense = {
            "name": "Alice",
            "category": "alimentacao",
            "sensitive": {"card": "4532 1111 2222 3333", "cpf": "123.456.789-00"},
        }
        sanitized = sanitizar_despesa_para_llm(expense)
        self.assertEqual(sanitized["sensitive"]["card"], "**** **** **** 3333")
        self.assertEqual(sanitized["sensitive"]["cpf"], "***.***.***-00")

    def test_agent_uses_gemini_result_when_response_is_confident(self):
        agent = AgentCore(Path("blueprint.md"), gemini_client=StubGeminiSuccess())
        result = agent.analyze_expense(
            {
                "category": "alimentacao",
                "amount": 45.0,
                "metadata": {},
                "sensitive": {"card": "4532 1111 2222 3333"},
            }
        )

        self.assertEqual(result["decision_source"], "gemini")
        self.assertEqual(result["audit_result"].status, "APROVADA")

    def test_agent_routes_to_manual_review_on_low_confidence(self):
        agent = AgentCore(Path("blueprint.md"), gemini_client=StubGeminiLowConfidence())
        result = agent.analyze_expense(
            {
                "category": "alimentacao",
                "amount": 45.0,
                "metadata": {},
                "sensitive": {"card": "4532 1111 2222 3333"},
            }
        )

        self.assertIn("REVIS", result["audit_result"].status.upper())

    def test_polish_business_text_does_not_corrupt_words(self):
        agent = AgentCore(Path("blueprint.md"), gemini_client=StubGeminiSuccess())
        text = "A categoria da despesa taxi nao possui diretriz explicita."
        polished = agent._polish_business_text(text)
        self.assertIn("categoria", polished)
        self.assertNotIn("categoranalise", polished)

    def test_agent_falls_back_to_local_auditor_when_gemini_fails(self):
        agent = AgentCore(Path("blueprint.md"), gemini_client=StubGeminiError())
        result = agent.analyze_expense(
            {
                "category": "alimentacao",
                "amount": 120.0,
                "metadata": {},
                "sensitive": {"card": "4532 1111 2222 3333"},
            }
        )

        self.assertEqual(result["decision_source"], "fallback_local")
        self.assertEqual(
            result["audit_result"].status,
            "REPROVADA - O valor excede o limite estabelecido no Blueprint",
        )


if __name__ == "__main__":
    unittest.main()
