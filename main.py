"""Agente Auditor de Despesas Corporativas.

Rodar este arquivo inicia um prompt simples para enviar despesas ao agente.
Alterações em `blueprint.md` são aplicadas imediatamente.
"""

from pathlib import Path

from src.auditor import AuditResult, ExpenseAuditor
from src.blueprint_parser import BlueprintRules, load_blueprint
from src.hot_reload import BlueprintWatcher


BLUEPRINT_PATH = Path(__file__).parent / "blueprint.md"


class AgentApp:
    def __init__(self, blueprint_path: Path):
        self.blueprint_path = blueprint_path
        self.rules = self._load_rules()
        self.auditor = ExpenseAuditor(self.rules)
        self.watcher = BlueprintWatcher(self.blueprint_path, self._reload_rules)

    def _load_rules(self) -> BlueprintRules:
        rules = load_blueprint(self.blueprint_path)
        print(f"[hot-reload] Regras recarregadas: {rules}")
        return rules

    def _reload_rules(self) -> None:
        self.rules = self._load_rules()
        self.auditor = ExpenseAuditor(self.rules)

    def run(self) -> None:
        self.watcher.start()
        print("Agente Auditor de Despesas (Ctrl+C para sair)")
        try:
            while True:
                expense = self._prompt_expense()
                result = self.auditor.audit(expense)
                self._print_result(result, expense)
        except KeyboardInterrupt:
            print("\nEncerrando agente.\n")
        finally:
            self.watcher.stop()

    def _prompt_expense(self) -> dict:
        print("\n--- Novo lançamento ---")
        category = input("Categoria (alimentacao/hospedagem/outro): ").strip()
        amount = input("Valor (ex: 79.90): ").strip().replace(",", ".")
        cep = None
        if category.lower().startswith("hospedagem"):
            cep = input("CEP do hotel (opcional): ").strip()

        card = input("Cartão/CPF (será mascarado): ").strip()

        return {
            "category": category,
            "amount": float(amount) if amount else 0.0,
            "metadata": {"cep": cep},
            "sensitive": {"card": card},
        }

    def _print_result(self, result: AuditResult, expense: dict) -> None:
        card = expense.get("sensitive", {}).get("card")
        card_masked = card[-4:].rjust(len(card), "*") if card else ""
        print("\n====== Resultado ======")
        print(result.response)
        print(f"Cartão/CPF: {card_masked}")
        print("======================\n")


if __name__ == "__main__":
    AgentApp(BLUEPRINT_PATH).run()
