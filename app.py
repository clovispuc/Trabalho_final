"""Dashboard Streamlit para o Agente Auditor de Despesas."""

from pathlib import Path
import json

import streamlit as st

from src.agent_core import AgentCore
from src.validators import mascarar_dados_sensiveis


def load_expenses(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def render_expense_details(expense: dict) -> None:
    metadata = expense.get("metadata", {})
    category = expense.get("category", "-")
    card = expense.get("sensitive", {}).get("card", "")
    breakdown = expense.get("breakdown", [])

    st.write("**Detalhes da despesa:**")
    st.write(f"- ID da despesa: **{expense.get('expense_id', '-')}**")
    st.write(f"- ID do colaborador: **{expense.get('employee_id', '-')}**")
    st.write(f"- Nome: **{expense.get('name', '-')}**")
    st.write(f"- Categoria: **{category}**")
    st.write(f"- Valor total: **R$ {expense.get('amount', 0):.2f}**")
    st.write(f"- Data: **{metadata.get('date', '-')}**")
    st.write(f"- Cidade: **{metadata.get('city', '-')}**")
    st.write(f"- Departamento: **{metadata.get('department', '-')}**")
    st.write(f"- Centro de custo: **{metadata.get('cost_center', '-')}**")
    st.write(f"- Fornecedor: **{metadata.get('vendor', '-')}**")
    st.write(f"- Aprovador: **{metadata.get('approver', '-')}**")
    st.write(f"- Cartao/CPF: **{mascarar_dados_sensiveis(card)}**")
    st.write(f"- Descricao: **{metadata.get('description', '-')}**")

    if breakdown:
        st.markdown("### Composicao do valor")
        st.write(f"- Total informado: **R$ {expense.get('amount', 0):.2f}**")
        total_breakdown = sum(float(item.get("total", 0)) for item in breakdown)
        st.write(f"- Total detalhado: **R$ {total_breakdown:.2f}**")

        for item in breakdown:
            description = item.get("item", "-")
            quantity = item.get("quantity", 0)
            unit_cost = float(item.get("unit_cost", 0))
            total = float(item.get("total", 0))
            st.write(f"- {description}: **{quantity} x R$ {unit_cost:.2f} = R$ {total:.2f}**")

    if category in {"viagem", "eventos"}:
        st.markdown("### Detalhamento do gasto")

        if category == "viagem":
            st.write(f"- Tipo de gasto: **Hospedagem / deslocamento corporativo**")
            st.write(f"- CEP de referencia: **{metadata.get('cep', 'Nao informado')}**")
            st.write(f"- Finalidade da viagem: **{metadata.get('description', '-')}**")
            st.write(
                f"- Contexto financeiro: **Centro de custo {metadata.get('cost_center', '-')} | "
                f"Fornecedor {metadata.get('vendor', '-')}**"
            )

        if category == "eventos":
            st.write(f"- Tipo de gasto: **Participacao ou estrutura de evento corporativo**")
            st.write(f"- Finalidade do evento: **{metadata.get('description', '-')}**")
            st.write(f"- Unidade responsavel: **{metadata.get('department', '-')}**")
            st.write(
                f"- Contexto financeiro: **Centro de custo {metadata.get('cost_center', '-')} | "
                f"Fornecedor {metadata.get('vendor', '-')}**"
            )


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

        with st.expander(f"{idx + 1}. {name} - {category} - R$ {amount:.2f}"):
            render_expense_details(expense)

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
