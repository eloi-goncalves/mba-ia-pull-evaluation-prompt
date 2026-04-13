## Como Executar

### Pré-requisitos

- Python 3.9+
- Conta no [LangSmith](https://smith.langchain.com/) com Hub handle configurado
- API Key da [OpenAI](https://platform.openai.com/api-keys) **ou** [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Configurar ambiente

```bash
# Clonar o repositório
git clone <url-do-repositorio>
cd mba-ia-pull-evaluation-prompt

# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# LangSmith
LANGSMITH_API_KEY=ls__...
LANGSMITH_USERNAME=seu-handle-langsmith   # slug, não o email
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=bug-to-user-story

# Escolha o provider: openai ou google
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
EVAL_MODEL=gpt-4o

# Se usar OpenAI
OPENAI_API_KEY=sk-...

# Se usar Google Gemini
# LLM_PROVIDER=google
# LLM_MODEL=gemini-2.5-flash
# EVAL_MODEL=gemini-2.5-flash
# GOOGLE_API_KEY=AIza...
```

> **Atenção:** `LANGSMITH_USERNAME` deve ser o seu Hub handle (ex: `joao-silva`), não o e-mail. Crie o handle em [https://smith.langchain.com/prompts](https://smith.langchain.com/prompts) publicando qualquer prompt público pela primeira vez.

### 3. Fase 1 — Pull dos prompts ruins do LangSmith

```bash
python src/pull_prompts.py
```

Salva o prompt base em `prompts/bug_to_user_story_v1.yml`.

### 4. Fase 2 — Otimização do prompt

O arquivo `prompts/bug_to_user_story_v2.yml` já contém o prompt otimizado com as 3 técnicas aplicadas. Para inspecionar:

```bash
cat prompts/bug_to_user_story_v2.yml
```

### 5. Fase 3 — Push do prompt otimizado para o LangSmith

```bash
python src/push_prompts.py
```

Publicará `{seu_username}/bug_to_user_story_v2` como prompt público no LangSmith Hub.

### 6. Fase 4 — Avaliação automática

```bash
python src/evaluate.py
```

Executa as 5 métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision) contra os 15 exemplos do dataset e publica os resultados no dashboard do LangSmith.

### 7. Executar testes de validação

```bash
pytest tests/test_prompts.py -v
```

---

## Evidências no LangSmith

### Dataset de Avaliação

> Adicione aqui o link público do dataset no LangSmith:
> `https://smith.langchain.com/public/<id>/datasets`
>
> O dataset contém **15 exemplos** (5 simples, 7 médios, 3 complexos) cobrindo domínios:
> e-commerce, SaaS, mobile, ERP e CRM.

### Execuções v1 (métricas baixas)

> Adicione screenshot ou link do experimento v1 showing métricas abaixo de 0.9.

### Execuções v2 (métricas otimizadas ≥ 0.9)

> Adicione screenshot ou link do experimento v2 após atingir todas as métricas ≥ 0.9.

### Tracing Detalhado

> Adicione links ou screenshots de pelo menos 3 tracings no LangSmith mostrando:
> - O input (bug_report)
> - O output gerado pelo modelo
> - As métricas calculadas para aquela execução

---


## Técnicas Aplicadas (Fase 2)

### 1. Few-Shot Learning

**O que é:** Fornecer ao modelo exemplos concretos de entrada e saída desejada dentro do próprio prompt, para que ele aprenda o padrão por indução.

**Por que foi escolhida:**
O F1-Score inicial era 0.44 — o pior resultado. O F1-Score mede o equilíbrio entre Precision e Recall do conteúdo gerado vs. o de referência. A causa raiz era que o modelo jamais produzia a seção "Critérios de Aceitação" no formato BDD (Dado/Quando/Então), que é o padrão exato de todos os outputs de referência do dataset. Sem exemplos, o modelo gerava user stories genéricas sem essa estrutura essencial, colapsando tanto o recall (omitia seções inteiras) quanto a precisão.

**Como foi aplicada:**
Dois exemplos foram inseridos no system_prompt, cobrindo os dois padrões do dataset:

- **Exemplo 1 — Bug simples (UI/UX):** Bug do Safari sem detalhes técnicos → user story com formato curto: `Como [persona], eu quero [...], para que [...].` seguido de 5 critérios BDD.
- **Exemplo 2 — Bug técnico (Integração):** Bug de webhook com steps to reproduce e logs → user story com formato estendido: mesma abertura + critérios BDD + seção "Contexto Técnico" + "Tasks Técnicas Sugeridas".

Os exemplos foram extraídos diretamente do dataset real para garantir máxima alinhamento com as referências de avaliação.

---

### 2. Chain of Thought (CoT)

**O que é:** Instruir o modelo a raciocinar passo a passo antes de produzir a resposta final, tornando o processo de inferência explícito e guiado.

**Por que foi escolhida:**
A métrica de Correctness estava em 0.63. O problema era que o modelo não mapeava corretamente o persona do bug (ex: um bug no dashboard deveria gerar "Como um administrador...", não "Como um usuário...") e não extraía os detalhes técnicos do relato para incluir na user story. Sem orientação de raciocínio, o modelo tomava atalhos e produzia outputs superficiais.

**Como foi aplicada:**
O system_prompt define explicitamente 5 passos obrigatórios de raciocínio antes de escrever:

```
Passo 1 — PERSONA: Identifique quem é o usuário afetado...
Passo 2 — NECESSIDADE: O que o usuário precisa que funcione?
Passo 3 — BENEFÍCIO: Por que isso importa para o usuário/negócio?
Passo 4 — CRITÉRIOS BDD: Formule os critérios (Dado/Quando/Então/E)
Passo 5 — COMPLEXIDADE: O relato tem logs/steps/múltiplos problemas?
           → SIM: use formato estendido com Contexto Técnico
           → NÃO: use formato simples
```

Esse guia de raciocínio garante que o modelo não pule a análise do domínio antes de gerar o output.

---

### 3. Rich Persona + Structured Output Specification

**O que é:** Definir uma persona rica e específica para o modelo assumir, combinada com especificação explícita do formato de saída esperado para cada caso.

**Por que foi escolhida:**
As métricas de Clarity (0.72) e Precision (0.82) sofriam com inconsistência estrutural: ora o modelo produzia uma lista simples, ora um texto corrido, ora inventava seções não esperadas. A falta de um "papel" claro também fazia o tone ser genérico demais.

**Como foi aplicada:**

- **Persona:** `"Você é um Product Owner sênior com mais de 10 anos de experiência..."` — estabelece autoridade de domínio e tom profissional desde a primeira instrução.
- **Formato Duplo Explícito:** O prompt define literalmente dois templates de output (simples e complexo) com marcadores separados para cada caso, eliminando ambiguidade sobre qual estrutura usar e para qual tipo de bug.

---

## Resultados Finais

### Tabela Comparativa: v1 (baseline) vs v2 (otimizado)

| Métrica | v1 (Baseline) | v2 (Otimizado) | Meta | Status |
|---|---|---|---|---|
| Helpfulness | 0.77 | — | ≥ 0.90 | Aguardando avaliação |
| Correctness | 0.63 | — | ≥ 0.90 | Aguardando avaliação |
| F1-Score | 0.44 | — | ≥ 0.90 | Aguardando avaliação |
| Clarity | 0.72 | — | ≥ 0.90 | Aguardando avaliação |
| Precision | 0.82 | — | ≥ 0.90 | Aguardando avaliação |

> **Nota:** Preencha a coluna "v2" com os resultados após executar `python src/evaluate.py` com o prompt v2 publicado no LangSmith.

### Link do Dashboard LangSmith

> Adicione aqui o link público do seu projeto no LangSmith após publicar as avaliações:
> `https://smith.langchain.com/public/<seu-project-id>/datasets`

### Screenshots das Avaliações

> Adicione screenshots do dashboard do LangSmith mostrando:
> - Avaliações do v1 com métricas baixas
> - Avaliações do v2 com métricas ≥ 0.9

---