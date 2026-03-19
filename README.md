# Agente Auditor de Despesas Corporativas

Projeto de DevOps em IA Generativa com foco em hot-reload semantico, governanca por texto e auditoria automatizada de despesas corporativas.

## Visao geral
O sistema analisa despesas a partir de diretrizes definidas em `blueprint.md`. O motor principal usa Gemini para gerar a decisao final em JSON estruturado, com fallback local para manter a aplicacao operante em caso de falha da API ou baixa confianca.

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
4. A aplicacao valida a resposta, aplica revisao manual em caso de incerteza e formata a mensagem final com linguagem mais comercial.
5. Se a API falhar, o auditor local assume a decisao.

## Regras de negocio atuais
- Alimentacao: despesas equivalentes a `almoco de negocios` e `jantar de negocios` seguem o limite de R$ 80,00.
- Hospedagem: despesas de `viagem` usam a referencia regional por CEP com tolerancia de 20% acima da media.
- Eventos: permanecem como categoria distinta e atualmente tendem a revisao manual no fluxo local.
- Categorias sem diretriz suficiente seguem para `REVISÃO MANUAL`.

## Base de dados
O arquivo `expenses_data.json` foi ampliado com uma base mais realista:
- nomes completos de colaboradores
- varias despesas por usuario
- categorias corporativas como `eventos`, `viagem`, `almoco de negocios` e `jantar de negocios`
- metadados adicionais como cidade, departamento, descricao e CEP quando aplicavel

Exemplos incluidos:
- despesas aprovadas de alimentacao dentro do limite
- despesas reprovadas por excesso de valor
- despesas de viagem com avaliacao por CEP
- despesas de eventos para revisao manual

## Configuracao
Defina a chave do Gemini em ambiente local:

```powershell
$env:GEMINI_API_KEY="sua-chave"
```

Ou use um arquivo `.env` local para o `docker compose`.

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

## Hot-reload
Ao editar `blueprint.md`, o comportamento do agente muda sem necessidade de recompilar a aplicacao. Isso permite demonstrar governanca de IA baseada em texto.

## Testes
Os testes cobrem:
- extracao das regras do blueprint
- auditoria local para alimentacao e hospedagem
- mascaramento de cartao e CPF
- fallback local quando Gemini falha
- revisao manual por baixa confianca
- mapeamento das categorias corporativas mais realistas
