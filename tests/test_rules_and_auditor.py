import unittest
from pathlib import Path

from src.auditor import ExpenseAuditor
from src.blueprint_parser import load_blueprint


class TestBlueprintAndAuditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_blueprint(Path('blueprint.md'))
        cls.auditor = ExpenseAuditor(cls.rules)

    def test_parser_extracts_core_rules(self):
        self.assertEqual(self.rules.alimentacao_limite, 80.0)
        self.assertTrue(self.rules.hospedagem_deve_usar_cep)
        self.assertEqual(self.rules.hospedagem_multiplicador, 1.2)
        self.assertEqual(self.rules.fallback_status, 'REVISÃO MANUAL')

    def test_alimentacao_above_limit_is_rejected_with_exact_status(self):
        result = self.auditor.audit({
            'category': 'alimentacao',
            'amount': 120.0,
            'metadata': {},
            'sensitive': {'card': '4532 1111 2222 3333'},
        })
        self.assertEqual(result.status, 'REPROVADA - O valor excede o limite estabelecido no Blueprint')

    def test_hospedagem_uses_cep_average_with_20_percent_margin(self):
        approved = self.auditor.audit({
            'category': 'hospedagem',
            'amount': 95.0,
            'metadata': {'cep': '01000-000'},
        })
        rejected = self.auditor.audit({
            'category': 'hospedagem',
            'amount': 100.0,
            'metadata': {'cep': '01000-000'},
        })

        self.assertEqual(approved.status, 'APROVADA')
        self.assertEqual(rejected.status, 'REPROVADA')

    def test_unknown_category_falls_back_to_manual_review(self):
        result = self.auditor.audit({'category': 'outro', 'amount': 10})
        self.assertEqual(result.status, 'REVISÃO MANUAL')


if __name__ == '__main__':
    unittest.main()
