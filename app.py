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

    st.sidebar.header("Configuração")
    st.sidebar.markdown(f"- Blueprint: `{blueprint_path.name}`")
    st.sidebar.markdown(f"- Dados: `{data_path.name}`")

    expenses = load_expenses(data_path)
    agent = AgentCore(blueprint_path)

    st.markdown("---")
    st.markdown("## Despesas")

    for idx, expense in enumerate(expenses):
        name = expense.get("name", "-")
        category = expense.get("category", "-")
        amount = expense.get("amount", 0)
        card = expense.get("sensitive", {}).get("card", "")
        card_masked = mascarar_dados_sensiveis(card)

        with st.expander(f"{idx+1}. {name} — {category} — R$ {amount:.2f}"):
            st.write("**Detalhes da despesa:**")
            st.write(f"- Nome: **{name}**")
            st.write(f"- Categoria: **{category}**")
            st.write(f"- Valor: **R$ {amount:.2f}**")
            st.write(f"- Cartão/CPF: **{card_masked}**")

            if st.button("Processar Auditoria com Agente IA", key=f"audit_{idx}"):
                result = agent.analyze_expense(expense)
                audit_result = result["audit_result"]
                llm_prompt = result["llm_prompt"]
                llm_response = result["llm_response"]

                st.markdown("---")
                st.markdown("### Resultado da Auditoria")
                st.write(f"- **Status:** {audit_result.status}")
                st.write(f"- **Motivo:** {audit_result.reason}")
                st.write(f"- **Resposta do Agente:**")
                st.code(audit_result.response)

                st.markdown("---")
                st.markdown("### (Simulação LLM)")
                st.write("**Prompt enviado ao LLM (para debug):**")
                st.code(llm_prompt)
                st.write("**Resposta simulada do LLM:**")
                st.code(llm_response)


if __name__ == "__main__":
    main()
