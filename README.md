# Agente Auditor de Despesas Corporativas (RPA)

Projeto de DevOps em IA Generativa com foco em **Hot-Reload Semântico**.

## Objetivo
O agente deve adaptar seu comportamento imediatamente quando o conteúdo de `blueprint.md` é alterado, sem precisar reiniciar a aplicação.

## Arquitetura
- **`blueprint.md`**: constituição do agente; define regras e diretrizes.
- **`src/blueprint_parser.py`**: interpreta o Markdown e extrai regras.
- **`src/auditor.py`**: aplica as regras aos lançamentos de despesas.
- **`src/hot_reload.py`**: monitora `blueprint.md` e recarrega as regras quando o arquivo muda.
- **`main.py`**: interface de linha de comando para testar o agente.

## Como rodar
1. Instale Python 3.11+ (recomendado).
2. Execute:

```bash
python main.py
```

O agente entrará em modo interativo. Cada vez que você editar `blueprint.md` e salvar, as regras serão recarregadas em tempo real.

## Como testar
1. Execute `python main.py`.
2. Insira uma despesa nos formatos pedidos.
3. Altere `blueprint.md` (por exemplo, altere o limite de alimentação) e salve.
4. Faça nova entrada; o comportamento mudará imediatamente.

## Usando Docker
1. Construa e inicie o serviço:

```bash
docker compose up --build
```

2. Acesse o dashboard em http://localhost:8501

> O arquivo `blueprint.md` (e `expenses_data.json`) são montados como volumes, então qualquer alteração se reflete imediatamente no container.
