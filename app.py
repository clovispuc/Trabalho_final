"""Dashboard Streamlit para o Agente Auditor de Despesas."""

from pathlib import Path
import json

import streamlit as st

from src.agent_core import AgentCore
from src.validators import mascarar_dados_sensiveis


def load_expenses(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    st.set_page_config(page_title="Auditor de Despesas (RPA)", layout="wide")
    st.title("Agente Auditor de Despesas Corporativas")

    data_path = Path(__file__).parent / "expenses_data.json"
    blueprint_path = Path(__file__).parent / "blueprint.md"

    agent = AgentCore(blueprint_path)
    expenses = load_expenses(data_path)

    st.sidebar.header("Configuracao")
    st.sidebar.markdown(f"- Blueprint: `{blueprint_path.name}`")
    st.sidebar.markdown(f"- Dados: `{data_path.name}`")
    st.sidebar.markdown(
        "- Motor de decisao: `Gemini`" if agent.is_gemini_configured() else "- Motor de decisao: `Fallback local`"
    )

    if not agent.is_gemini_configured():
        st.warning(
            "GEMINI_API_KEY nao configurada. O sistema continua funcionando com o auditor local como fallback."
        )

    st.markdown("---")
    st.markdown("## Despesas")

    for idx, expense in enumerate(expenses):
        name = expense.get("name", "-")
        category = expense.get("category", "-")
        amount = expense.get("amount", 0)
        card = expense.get("sensitive", {}).get("card", "")
        card_masked = mascarar_dados_sensiveis(card)

        with st.expander(f"{idx + 1}. {name} - {category} - R$ {amount:.2f}"):
            st.write("**Detalhes da despesa:**")
            st.write(f"- Nome: **{name}**")
            st.write(f"- Categoria: **{category}**")
            st.write(f"- Valor: **R$ {amount:.2f}**")
            st.write(f"- Cartao/CPF: **{card_masked}**")

            if st.button("Processar Auditoria com Agente IA", key=f"audit_{idx}"):
                result = agent.analyze_expense(expense)
                audit_result = result["audit_result"]

                st.markdown("---")
                st.markdown("### Resultado da Auditoria")
                st.write(f"- **Status:** {audit_result.status}")
                st.write(f"- **Motivo:** {audit_result.reason}")
                st.write(f"- **Canal de analise:** {result['decision_source']}")
                st.write(f"- **Observacao operacional:** {result['decision_detail']}")
                st.write("**Resposta do Agente:**")
                st.code(audit_result.response)


if __name__ == "__main__":
    main()
