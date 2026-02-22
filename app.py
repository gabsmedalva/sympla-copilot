import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from google import genai
import json

# 1. Conexão Segura via Secrets do Streamlit
API_KEY = st.secrets["GEMINI_API_KEY"] 
client_genai = genai.Client(api_key=API_KEY)

# Lendo o crachá do BigQuery
cred_json = json.loads(st.secrets["gcp_service_account"]["json_key"])
credentials = service_account.Credentials.from_service_account_info(cred_json)
client_bq = bigquery.Client(credentials=credentials, project=credentials.project_id)

# 2. Configuração da Página e Interface
st.set_page_config(page_title="Sympla AI Copilot", page_icon="🎫", layout="wide")
st.title("🤖 Sympla Intelligence Copilot")
st.write("Olá, CEO. O que gostaria de analisar sobre o fechamento de vendas?")

# 3. Prompt Sênior (Atualizado com Roteamento e Matriz BCG)
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

REGRAS DE CÁLCULO FINANCEIRO E FORECASTING (CRÍTICO):
A tabela fato possui uma mistura de dados reais e projeções de Machine Learning. O mês atual de fechamento do CEO é FEVEREIRO DE 2034.

1. DADOS REAIS (Histórico): Tudo que ocorreu até Fevereiro de 2034 (inclusive) é dado real e consolidado. Para perguntas sobre o passado ou o mês atual, você DEVE OBRIGATORIAMENTE usar o filtro `flag_previsao = 0` na query SQL.
2. DADOS DE FORECAST (Projeção ML): Tudo de Março de 2034 até Dezembro de 2034 é predição gerada por modelo de Machine Learning. Se o CEO perguntar sobre o futuro, expectativa ou projeções, você DEVE OBRIGATORIAMENTE usar o filtro `flag_previsao = 1`.
3. NUNCA misture `flag_previsao = 0` e `flag_previsao = 1` na mesma soma (SUM) sem separá-los explicitamente.
4. Evolução MoM (Month-over-Month): Comparar o mês atual (Fevereiro de 2034) contra o mês imediatamente anterior (Janeiro de 2034).
5. Evolução YoY (Year-over-Year): Comparar o mês atual (Fevereiro de 2034) contra o mesmo mês do ano passado (Fevereiro de 2033).

REGRAS DA MATRIZ BCG (ESTRATÉGIA DE PORTFÓLIO):
Quando o CEO mencionar "Matriz BCG", "Estrelas", "Vacas Leiteiras", "Interrogações" ou "Abacaxis/Cães", construa a query SQL calculando os dois eixos da matriz APENAS COM DADOS REAIS (`flag_previsao = 0`):
- EIXO DE VOLUME: A soma total de `vr_venda` em Fev/2034.
- EIXO DE CRESCIMENTO: O crescimento percentual YoY (Fev/2034 vs Fev/2033).
Use CTEs para calcular a média geral de volume e de crescimento. A classificação segue a regra:
- ESTRELA: Volume ACIMA da média e Crescimento ACIMA da média.
- VACA LEITEIRA: Volume ACIMA da média e Crescimento ABAIXO da média.
- INTERROGAÇÃO: Volume ABAIXO da média e Crescimento ACIMA da média.
- ABACAXI/CÃO: Volume ABAIXO da média e Crescimento ABAIXO da média.

REGRAS DE DECISÃO DE ROTEAMENTO (MUITO IMPORTANTE):
1. Se a pergunta exigir DADOS do banco, retorne APENAS o código SQL puro. Sem formatação markdown (```sql) e sem explicações. Apenas o código.
2. Se a pergunta NÃO exigir consulta ao banco, retorne EXATAMENTE a palavra: TEXTO_COMUM
"""

# 4. Motor do Chat (Atualizado com Botão, Input e Gráficos)
sugestao_ceo = "Onde devo concentrar os esforços de expansão de vendas baseando-se na Matriz BCG e no crescimento YoY de feveriro de 2034?"
pergunta_usuario = None

# Botão de Sugestão
if st.button(f"💡 Sugestão do dia: {sugestao_ceo}"):
    pergunta_usuario = sugestao_ceo

# Caixa de texto normal
prompt_digitado = st.chat_input("Digite sua pergunta ou clique na sugestão acima...")
if prompt_digitado:
    pergunta_usuario = prompt_digitado

# Se o botão foi clicado OU o usuário digitou algo, roda a análise
if pergunta_usuario:
    st.chat_message("user").write(pergunta_usuario)
    
    with st.spinner("Analisando a intenção da pergunta..."):
        resposta_ia = client_genai.models.generate_content(
            model='gemini-2.5-pro',
            contents=f"{schema_prompt}\nPergunta do CEO: {pergunta_usuario}"
        )
        decisao = resposta_ia.text.replace('```sql', '').replace('```', '').strip()
    
    # Roteamento: Bate-papo vs Dados
    if decisao == "TEXTO_COMUM":
        with st.spinner("Respondendo diretamente..."):
            resposta_direta = client_genai.models.generate_content(
                model='gemini-2.5-pro',
                contents=f"Você é o Copiloto de Inteligência Sênior da Sympla. O CEO (seu chefe) acabou de dizer: '{pergunta_usuario}'. Responda DIRETAMENTE a ele em primeira pessoa, de forma executiva, breve e natural. Não crie opções de resposta, não explique o que está fazendo. Apenas assuma o personagem e responda."
            )
            st.chat_message("assistant").write(resposta_direta.text)
            
    else:
        # Modo Banco de Dados (SQL Gerado)
        with st.expander("Ver código SQL gerado"):
            st.code(decisao, language="sql")
            
        with st.spinner("Consultando o banco de dados..."):
            try:
                df_resultado = client_bq.query(decisao).to_dataframe()
                st.dataframe(df_resultado)
                
                # --- NOVIDADE: Geração Automática de Gráfico ---
                if not df_resultado.empty and len(df_resultado.columns) >= 2:
                    try:
                        # Tenta pegar a primeira coluna de texto e a primeira numérica
                        col_cat = df_resultado.select_dtypes(include=['object', 'string']).columns[0]
                        col_num = df_resultado.select_dtypes(include=['number']).columns[0]
                        st.bar_chart(data=df_resultado, x=col_cat, y=col_num)
                    except Exception:
                        pass # Se não conseguir plotar, segue sem travar o app
                
                with st.spinner("Analisando resultados financeiros..."):
                    resposta_final = client_genai.models.generate_content(
                        model='gemini-2.5-pro',
                        contents=f"O CEO perguntou: {pergunta_usuario}. Os dados retornados do BigQuery foram: {df_resultado.to_dict()}. Escreva uma resposta analítica e direta baseada APENAS nesses números, focando em responder à dúvida principal."
                    )
                    st.chat_message("assistant").write(resposta_final.text)
                    
            except Exception as e:
                st.error(f"Ops! Algo deu errado na consulta ao banco: {e}")