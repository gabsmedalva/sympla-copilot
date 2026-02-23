# 🤖 Sympla Intelligence Copilot

Um assistente virtual conversacional de Inteligência Artificial desenhado para a diretoria da Sympla. O Copilot atua como um analista de dados autônomo, capaz de traduzir perguntas de negócios em linguagem natural (Text-to-SQL), consultar o Data Warehouse no Google BigQuery em tempo real e devolver insights estratégicos e visualizações gráficas.

## 🎯 Visão Geral do Projeto
Este projeto resolve o gargalo de relatórios estáticos e demandas *ad-hoc* da equipe de dados. Através de um painel interativo, o CEO pode realizar perguntas complexas sobre o fechamento de vendas (ex: evolução MoM, YoY e Matriz BCG) e obter respostas validadas matematicamente em segundos.

## Arquitetura e Fluxo de Execução
A aplicação foi construída em **Python + Streamlit** e utiliza o modelo **Gemini 2.5 Pro** como motor cognitivo. O fluxo de execução obedece à seguinte arquitetura:

1. **Roteamento de Intenção (Intent Routing):** Quando o usuário envia uma mensagem, o LLM avalia se a requisição exige dados estruturados ou se é uma interação comum.
   * Se for uma conversa comum, o assistente responde diretamente.
   * Se exigir dados, o LLM entra no modo *Text-to-SQL*.
2. **Engenharia de Prompt (Regras de Negócio):** O modelo possui um contexto rigoroso das regras da Sympla embutido no sistema, como:
   * Separação estrita entre dados realizados (`flag_previsao = 0`) e projeções de Machine Learning (`flag_previsao = 1`).
   * Cálculo dinâmico da **Matriz BCG** (Volume vs. Crescimento YoY) via CTEs em SQL.
3. **Consulta e Visualização:** O SQL gerado pelo LLM é executado no **Google BigQuery**. O resultado em formato tabular (Pandas DataFrame) é renderizado na tela, acompanhado de uma plotagem gráfica automática (Bar Chart).
4. **Síntese Analítica:** Os dados brutos retornados do banco são enviados de volta ao Gemini, que escreve um resumo executivo focando na resposta à pergunta original do CEO.

## Stack Tecnológica
* **Frontend/App:** Streamlit
* **LLM / GenAI:** Google Gemini 2.5 Pro (`google-genai`)
* **Data Warehouse:** Google BigQuery (`google-cloud-bigquery`)
* **Manipulação de Dados:** Pandas & PyArrow

## Como Executar Localmente

### 1. Clonar o Repositório e Instalar Dependências
```bash
git clone [https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git](https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git)
cd NOME_DO_REPOSITORIO
pip install -r requirements.txt
