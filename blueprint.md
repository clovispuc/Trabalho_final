# Blueprint: A "Constituição" do Nosso Agente de Despesas

## O Que é Este Projeto?
Sabe aquele trabalho chato do financeiro de ficar lendo nota fiscal de almoço, hotel e táxi dos funcionários para aprovar reembolso? Nós criamos um **Agente de IA** para fazer isso sozinho! 

A grande sacada (e o foco de DevOps do nosso trabalho) não é só usar a IA, mas **como nós controlamos a IA**. Este arquivo aqui (o `blueprint.md`) funciona como o "chefe" do agente. A IA só faz o que está escrito aqui. Se a gente mudar as regras neste arquivo, o agente muda de comportamento na mesma hora, sem precisarmos mexer no código Python.

## Como Montamos o Sistema (Arquitetura Simples)
Para o sistema funcionar direitinho na máquina de qualquer pessoa do grupo ou do professor, dividimos em algumas peças:

* **Docker e Docker Compose:** É a "caixa" onde tudo roda. Usamos um recurso chamado "Volumes" para conectar este arquivo `.md` direto na caixa. 
* **`app.py`:** É a telinha do nosso sistema (usamos Streamlit para ficar bonito e fácil).
* **`agent_core.py`:** É o "cérebro". O código que pega a nota fiscal e pede para a IA analisar. É aqui também que ficam as "ferramentas" da IA (como a nossa busca de CEP falsa).
* **`validators.py`:** É o nosso "guarda-costas". Antes de mostrar a resposta da IA na tela, esse código confere se a IA não vazou nenhum dado sensível.
* **`expenses_data.json`:** Nossas notas fiscais de mentirinha (dados sintéticos) para testar o robô.

---

## Diretrizes da IA (As Regras que o Agente DEVE Seguir)

Esta é a parte mais importante. O Agente de IA precisa ler e obedecer a estas regras para tomar decisões:

### 1. Regras de Dinheiro e Ferramentas
* **O Limite de Alimentação:** Para despesas de "Alimentação", o funcionário só pode gastar até **R$ 80,00** por dia. Se a nota for maior, o agente deve dar o status exato de: `REPROVADA - O valor excede o limite estabelecido no Blueprint`.
* **O Limite de Hospedagem (Uso de Ferramenta):** Quando a nota for de "Hospedagem", a IA **não pode adivinhar** se está caro. Ela deve acionar a nossa ferramenta de busca pelo CEP do hotel para descobrir o preço médio da região. O funcionário só pode gastar até **20% acima da média daquela região**. Se estourar esse limite de 20%, a nota é `REPROVADA`.

### 2. A Personalidade da IA
* Se a despesa for **Aprovada**, a IA deve responder de forma chique, muito formal e educada.
* Se a despesa for **Reprovada**, a IA deve ser empática (pedir desculpas), mas firme. **Atenção (Restrição de Saída):** A IA tem a obrigação de explicar para o funcionário qual foi a regra ou limite financeiro que ele quebrou.

### 3. Regras de Segurança e Ética
* **Proteção de Dados (LGPD):** É proibido mostrar o número do cartão de crédito ou CPF inteiro. A IA só pode mostrar os 4 últimos números (Ex: `Cartão final **** 3333`). Se a IA tentar vazar, nosso `validators.py` vai bloquear.
* **Segurança do Sistema:** A IA nunca deve mostrar chaves de API, senhas ou explicar como nosso código funciona por trás.
* **Se não souber, não invente (Fallback):** Se a IA ficar confusa ao ler uma nota fiscal (nota borrada ou categoria estranha), ela não pode adivinhar. Ela deve colocar a despesa como `REVISÃO MANUAL` para um humano olhar.

---

## Nossas Tarefas (User Stories / Tabela de Implementação)

| ID | Descrição (O que vamos fazer) | Critérios de Aceite (Como saber se deu certo) | Prioridade |
| :--- | :--- | :--- | :--- |
| **US01** | **Tela do Sistema (Dashboard)** | O arquivo `app.py` tem que mostrar uma telinha com a lista das notas fiscais e o status que a IA decidiu (Aprovada, Reprovada ou Revisão). | Alta |
| **US02** | **O Cérebro da IA (Motor Generativo)** | O `agent_core.py` precisa ler o JSON, aplicar as regras do dinheiro e responder com o tom de voz certo. | Alta |
| **US03** | **Esconder Dados Sensíveis (LGPD)** | O nosso código "guarda-costas" (`validators.py`) não pode deixar aparecer o número inteiro do cartão na tela. | Alta |
| **US04** | **Criar Despesas de Mentira (JSON)** | Ter um arquivo `expenses_data.json` pronto com notas de almoço e notas de hotel para testar o agente. | Alta |
| **US05** | **A Mágica da Atualização (Hot-Reload)** | Se a gente alterar o limite de R$ 80 direto neste arquivo `.md`, o sistema (no Docker) tem que atualizar sozinho, na hora! | Alta |
| **US06** | **Teste Rápido (Golden Dataset)** | Ter um testezinho escondido que roda antes de aplicarmos uma nova regra, garantindo que não quebramos o sistema. | Média |
| **US07** | **Bloquear "Golpes" na IA (Prompt Injection)**| O `validators.py` tem que impedir que uma frase estranha na nota tente hackear as regras do agente. | Média |
| **US08** | **Pedir Ajuda Humana (Fallback)** | Se a IA não tiver certeza do que está lendo, o sistema deve colocar como "Revisão Manual". | Média |
| **US09** | **Uso de Ferramenta (Busca de Preços Mock)** | O Agente deve pausar a análise da nota de hotel, chamar uma função no código Python passando o CEP, receber a média da região e calcular se o valor passou dos 20%. | Máxima |

---

## Como Vamos Apresentar pro Professor (Live Demo)

No dia da apresentação, vamos fazer este passo a passo para mostrar tudo o que aprendemos:

1. **A IA usando Ferramentas:** Vamos mostrar uma despesa de hotel cara no centro de SP. Vamos provar que a IA não "chutou" o valor, mas sim pediu para o Python olhar a média da região pelo CEP (Function Calling) antes de reprovar a nota.
2. **O Problema Inicial:** Vamos mostrar o funcionário "João" gastando R$ 120,00 no almoço. A IA vai mostrar que está **"Reprovada"** (porque o limite era R$ 80) e o cartão dele vai aparecer censurado (LGPD).
3. **A Mudança (Governança):** Vamos abrir este arquivo Markdown na frente da turma e mudar a regra de almoço para R$ 150,00. E vamos salvar o arquivo.
4. **A Mágica (Hot-Reload):** Vamos voltar na tela do sistema e ela vai atualizar sozinha. A nota do João vai passar para **"Aprovada"**, provando o poder de governar a IA apenas por texto, sem recompilar o código!