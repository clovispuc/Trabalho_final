# Agente Auditor de Despesas Corporativas

Projeto de DevOps em IA Generativa com foco em hot-reload semantico, governanca por texto e auditoria automatizada de despesas corporativas.

## Visao geral
O sistema analisa despesas a partir de diretrizes definidas em `blueprint.md`. O motor principal usa Gemini para gerar a decisao final em JSON estruturado, com fallback local para manter a aplicacao operante em caso de falha da API, resposta invalida ou baixa confianca.

## Aderencia ao trabalho
- Passo 1: o projeto possui um `blueprint.md` com diretrizes da IA, tom de voz, restricoes de linguagem, regras de seguranca e criterios de negocio.
- Passo 2: a arquitetura e modular, com `app.py`, `src/agent_core.py`, `src/validators.py` e `expenses_data.json`.
- Passo 3: o projeto roda com Docker e Docker Compose, e o `blueprint.md` e montado como volume para demonstrar hot-reload de governanca.
- Passo 4: o repositorio entrega o codigo-fonte, o blueprint final e base suficiente para gerar video ou relatorio de demonstracao.

## Arquitetura
- `blueprint.md`: diretrizes corporativas e regras de negocio.
- `app.py`: dashboard Streamlit para demonstracao.
- `main.py`: interface de linha de comando.
- `src/agent_core.py`: orquestra Gemini, fallback local e polimento da resposta final.
- `src/gemini_client.py`: integracao com a API do Gemini.
- `src/auditor.py`: regras locais de aprovacao, reprovacao e revisao manual.
- `src/blueprint_parser.py`: leitura das regras declaradas no blueprint.
- `src/validators.py`: mascaramento de dados sensiveis e validacao do JSON retornado pela IA.
- `src/tools.py`: normalizacao de categorias e utilitarios.
- `expenses_data.json`: base sintetica de despesas para demonstracao.
- `tests/`: testes unitarios do parser, auditor, validadores e fluxo do agente.

## Como funciona
1. O sistema le a despesa e as diretrizes vigentes em `blueprint.md`.
2. Cartoes e CPFs sao mascarados antes do envio ao provedor externo.
3. O Gemini recebe a despesa saneada e responde em JSON estruturado.
4. A aplicacao valida a resposta, aplica revisao manual em caso de incerteza e formata a mensagem final com linguagem corporativa.
5. Se a API falhar, o auditor local assume a decisao.

## Regras de negocio atuais
- Alimentacao: despesas equivalentes a `almoco de negocios` e `jantar de negocios` seguem o limite de R$ 80,00.
- Hospedagem: despesas de `viagem` usam a referencia regional por CEP com tolerancia de 20% acima da media.
- Eventos: permanecem como categoria distinta e tendem a revisao manual quando nao houver politica financeira explicita.
- Categorias sem diretriz suficiente seguem para `REVISÃO MANUAL`.

## Base de dados
O arquivo `expenses_data.json` foi ampliado com uma base mais realista:
- nomes completos de colaboradores
- varias despesas por usuario
- categorias corporativas como `eventos`, `viagem`, `almoco de negocios` e `jantar de negocios`
- metadados adicionais como cidade, departamento, descricao e CEP quando aplicavel
- campos corporativos como `expense_id`, `employee_id`, `cost_center`, `vendor` e `approver`

Exemplos incluidos:
- despesas aprovadas de alimentacao dentro do limite
- despesas reprovadas por excesso de valor
- despesas de viagem com avaliacao por CEP
- despesas de eventos para revisao manual

## Configuracao
Cada colega deve criar seu proprio arquivo `.env` local a partir de [.env.example](c:/Users/clovi/OneDrive/Documentos/IA%20GENERATIVA/Trabalho_final/.env.example).

Exemplo:

```bash
cp .env.example .env
```

Depois, basta editar o `.env` e preencher a propria chave do Gemini.

Tambem e possivel definir a chave diretamente no ambiente local:

```powershell
$env:GEMINI_API_KEY="sua-chave"
```

O `docker compose` le automaticamente o `.env` local.

## Como rodar localmente
1. Instale Python 3.11+.
2. Instale as dependencias:

```bash
pip install -r requirements.txt
```

3. Configure `GEMINI_API_KEY`.
4. Execute:

```bash
python main.py
```

## Como rodar com Docker
1. Suba o servico:

```bash
docker compose up --build
```

2. Acesse:

```text
http://localhost:8502
```

O arquivo `blueprint.md` e a base `expenses_data.json` sao montados como volume, entao alteracoes nesses arquivos se refletem imediatamente no container.

## Como demonstrar
1. Abra `http://localhost:8502`.
2. Escolha uma despesa de alimentacao acima do limite e execute a analise.
3. Mostre a reprovacao com justificativa financeira.
4. Edite `blueprint.md` e altere o limite de R$ 80,00 para R$ 150,00.
5. Salve o arquivo sem alterar o codigo-fonte.
6. Reprocesse a mesma despesa e mostre a mudanca de comportamento.
7. Execute um caso de `viagem` com CEP informado para demonstrar a referencia regional.
8. Execute um caso de `eventos` para mostrar o encaminhamento para revisao manual.

## Hot-reload
Ao editar `blueprint.md`, o comportamento do agente muda sem necessidade de recompilar a aplicacao. Isso permite demonstrar governanca de IA baseada em texto, um dos pontos centrais do trabalho.

## Testes
Os testes cobrem:
- extracao das regras do blueprint
- auditoria local para alimentacao e hospedagem
- mascaramento de cartao e CPF
- fallback local quando Gemini falha
- revisao manual por baixa confianca
- mapeamento das categorias corporativas mais realistas

## Entrega final
Para a entrega academica, este repositorio deve ser acompanhado por:
- um video curto de demonstracao ou um relatorio
- evidencias da mudanca de comportamento apos a alteracao do `blueprint.md`
- o ZIP do projeto com a estrutura modularizada
