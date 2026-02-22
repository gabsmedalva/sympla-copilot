import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from google import genai
import json

# 1. Conexão Segura via Secrets do Streamlit
# O Streamlit vai buscar essa variável escondida no painel dele
API_KEY = st.secrets["GEMINI_API_KEY"] 
client_genai = genai.Client(api_key=API_KEY)

# Lendo o acesso do BigQuery
cred_json = json.loads(st.secrets["gcp_service_account"]["json_key"])
credentials = service_account.Credentials.from_service_account_info(cred_json)
client_bq = bigquery.Client(credentials=credentials, project=credentials.project_id)

# 2. Configuração da Página e Interface (Apenas UMA vez)
st.set_page_config(page_title="Sympla AI Copilot", page_icon="🎫", layout="wide")
st.title("🤖 Sympla Intelligence Copilot")
st.write("Olá, CEO. O que gostaria de analisar sobre o fechamento de vendas?")

# 3. Prompt Sênior (Atualizado com Roteamento)
schema_prompt = """
Você é o Copiloto de Inteligência de Dados Sênior da Sympla. O usuário interagindo com você é o CEO da empresa.

CENÁRIO DO NEGÓCIO:
Estamos no fechamento de Fevereiro de 2034. O objetivo do CEO é entender o desempenho de vendas do último mês para buscar direcionamento sobre onde concentrar os esforços de expansão no restante do ano. 

O banco de dados é um Star Schema no Google BigQuery, no dataset 'site-da-laica.sympla'.
ESTRUTURA DAS TABELAS (Todas as 5 são obrigatórias para os relacionamentos):
- Fato: fato_vendas_forecasting (sk_tempo, sk_localidade, sk_produtor, sk_evento, vr_venda, qt_ingresso, flag_previsao)
- Dim Tempo: dim_tempo (sk_tempo, ano, mes, trimestre, dt_venda)
- Dim Localidade: dim_localidade (sk_localidade, nm_localidade_estado)
- Dim Produtor: dim_produtor (sk_produtor, tp_tamanho_produtor, tp_produtor_canal_aquisicao)
- Dim Evento: dim_evento (sk_evento, nm_evento_classificacao_negocio)

REGRAS DE CÁLCULO FINANCEIRO (MUITO IMPORTANTE):
Quando o CEO perguntar sobre "evolução", "crescimento", "queda" ou "comparativo", você DEVE gerar o SQL calculando as seguintes métricas (usando subqueries ou CTEs):
1. Evolução MoM (Month-over-Month): Comparar o mês atual (Fevereiro de 2034) contra o mês imediatamente anterior (Janeiro de 2034).
2. Evolução YoY (Year-over-Year): Comparar o mês atual (Fevereiro de 2034) contra o mesmo mês do ano passado (Fevereiro de 2033).
3. Dados Históricos vs Projeção:
   - Histórico (Realizado): Tudo até Fev/2034 deve usar o filtro `flag_previsao = 0`.
   - Projeção (Forecast): Tudo de Março/2034 até Dez/2034 deve usar o filtro `flag_previsao = 1`.

REGRAS DA MATRIZ BCG (ESTRATÉGIA DE PORTFÓLIO):
Quando o CEO mencionar "Matriz BCG", "Estrelas", "Vacas Leiteiras", "Interrogações" ou "Abacaxis/Cães", você deve construir a query SQL calculando os dois eixos da matriz para a dimensão solicitada (Estados, Categorias de Evento ou Produtores):
- EIXO DE VOLUME (Share): A soma total de `vr_venda` em Fev/2034.
- EIXO DE CRESCIMENTO (Growth): O crescimento percentual YoY (Fev/2034 vs Fev/2033).
Use CTEs para calcular a média geral de volume e de crescimento. A classificação segue a regra:
- ESTRELA (Star): Volume ACIMA da média e Crescimento ACIMA da média.
- VACA LEITEIRA (Cash Cow): Volume ACIMA da média e Crescimento ABAIXO da média.
- INTERROGAÇÃO (Question Mark): Volume ABAIXO da média e Crescimento ACIMA da média.
- ABACAXI/CÃO (Dog): Volume ABAIXO da média e Crescimento ABAIXO da média.
O SQL deve retornar as colunas: Nome da Dimensão, Volume, % Crescimento e a Classificação BCG.

REGRAS DE DECISÃO DE ROTEAMENTO (MUITO IMPORTANTE):
1. Se a pergunta exigir DADOS do banco (ex: "Qual estado vendeu mais?", "Comparativo de vendas YoY", "Construa a Matriz BCG dos eventos"), retorne APENAS o código SQL puro. Sem formatação markdown (```sql) e sem explicações extras. Apenas o código.
2. Se a pergunta NÃO exigir consulta ao banco (ex: "Olá", "Tudo bem?", "Como você pode me ajudar?"), retorne EXATAMENTE a palavra: TEXTO_COMUM
"""

# 4. Motor do Chat (Atualizado com Lógica de Desvio)
pergunta_usuario = st.chat_input("Ex: Qual estado teve a maior venda em fev/2034?")

if pergunta_usuario:
    st.chat_message("user").write(pergunta_usuario)
    
    with st.spinner("Analisando a intenção da pergunta..."):
        resposta_ia = client_genai.models.generate_content(
            model='gemini-2.5-pro',
            contents=f"{schema_prompt}\nPergunta do CEO: {pergunta_usuario}"
        )
        decisao = resposta_ia.text.replace('```sql', '').replace('```', '').strip()
    
    # Roteamento: É só um bate-papo ou precisa de dados?
    if decisao == "TEXTO_COMUM":
        with st.spinner("Respondendo diretamente..."):
            resposta_direta = client_genai.models.generate_content(
                model='gemini-2.5-pro',
                contents=f"Você é o Copiloto de Inteligência Sênior da Sympla. O CEO (seu chefe) acabou de dizer: '{pergunta_usuario}'. Responda DIRETAMENTE a ele em primeira pessoa, de forma executiva, breve e natural. Não crie opções de resposta, não explique o que está fazendo. Apenas assuma o personagem e responda."
            )
            st.chat_message("assistant").write(resposta_direta.text)
            
    else:
        # Se não for texto comum, ele gerou SQL!
        with st.expander("Ver código SQL gerado"):
            st.code(decisao, language="sql")
            
        with st.spinner("Consultando o banco de dados..."):
            try:
                df_resultado = client_bq.query(decisao).to_dataframe()
                st.dataframe(df_resultado)
                
                with st.spinner("Analisando resultados financeiros..."):
                    resposta_final = client_genai.models.generate_content(
                        model='gemini-2.5-pro',
                        contents=f"O CEO perguntou: {pergunta_usuario}. Os dados retornados do BigQuery foram: {df_resultado.to_dict()}. Escreva uma resposta analítica e direta baseada APENAS nesses números."
                    )
                    st.chat_message("assistant").write(resposta_final.text)
            except Exception as e:
                st.error(f"Ops! Algo deu errado na consulta ao banco: {e}")