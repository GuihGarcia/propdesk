import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# 1. CONFIGURAÇÃO E TEMA DARK FORÇADO
st.set_page_config(page_title="PropDesk Pro", layout="wide")

st.markdown("""
    <style>
    /* Fundo principal e sidebar */
    [data-testid="stAppViewContainer"], [data-testid="stSidebar"] { background-color: #0e1117 !important; }
    /* Cards de métricas */
    div[data-testid="stMetric"] { 
        background-color: #1e2235 !important; 
        border: 1px solid #3d4466 !important; 
        padding: 15px !important; 
        border-radius: 10px !important; 
    }
    /* Cores de texto */
    h1, h2, h3, p, span, label { color: white !important; }
    div[data-testid="stMetricValue"] > div { color: #00ffcc !important; font-weight: bold ! dominance; }
    /* Inputs e botões */
    .stTextInput, .stNumberInput, .stSelectbox { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. BANCO DE DADOS
def load_data(file, columns):
    if os.path.exists(file):
        df = pd.read_csv(file)
        if 'Date' in df.columns: df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=columns)

acc_df = load_data('accounts.csv', ['Account', 'Group', 'Type_Owner', 'Size', 'Profit_Split'])
hist_df = load_data('history.csv', ['Date', 'Account', 'Type', 'Value'])

# 3. MENU LATERAL
st.sidebar.title("🚀 PropDesk v4.0")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "⚙️ Configurar Contas", "💸 Lançar Lucro/Perda"])

if menu == "📊 Dashboard":
    st.title("Dashboard de Contas")
    if acc_df.empty:
        st.warning("⚠️ Nenhuma conta ativa encontrada. Vá em 'Configurar Contas' para começar.")
    else:
        # Cálculos e Cards
        cap_total = acc_df['Size'].sum()
        if not hist_df.empty:
            df_m = hist_df.merge(acc_df, on='Account', how='inner')
            df_m['Net'] = df_m.apply(lambda x: x['Value'] * (x['Profit_Split']/100) if x['Type_Owner'] == 'Mesa' else x['Value'], axis=1)
            lucro_mes = df_m[df_m['Value'] > 0]['Value'].sum()
            perda_mes = df_m[df_m['Value'] < 0]['Value'].sum()
            liquido = df_m['Net'].sum()
        else:
            lucro_mes = perda_mes = liquido = 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("CAPITAL TOTAL", f"R$ {cap_total:,.2f}")
        c2.metric("TOTAL CONTAS", len(acc_df))
        c3.metric("LUCRO DO MÊS", f"R$ {lucro_mes:,.2f}")
        c4.metric("PERDA DO MÊS", f"R$ {abs(perda_mes):,.2f}")
        c5.metric("RESULTADO LÍQUIDO", f"R$ {liquido:,.2f}")
        
        if not hist_df.empty:
            st.markdown("---")
            df_equity = df_m.sort_values('Date').groupby('Date')['Value'].sum().cumsum().reset_index()
            st.plotly_chart(px.area(df_equity, x='Date', y='Value', title="Evolução Patrimonial", template="plotly_dark"), use_container_width=True)

elif menu == "⚙️ Configurar Contas":
    st.title("Configuração de Contas")
    with st.form("add_group"):
        st.subheader("Cadastrar Novo Grupo de Robôs")
        g_nome = st.text_input("Nome do Grupo (Ex: Apex 50k)")
        g_lista = st.text_area("Nomes dos Robôs (um por linha)")
        col1, col2 = st.columns(2)
        g_tipo = col1.selectbox("Origem", ["Mesa", "Pessoal"])
        g_split = col2.number_input("Sua Porcentagem (%)", value=80 if g_tipo == "Mesa" else 100)
        if st.form_submit_button("Salvar Grupo"):
            nomes = [n.strip() for n in g_lista.split('\n') if n.strip()]
            novos = pd.DataFrame([[n, g_nome, g_tipo, 50000, g_split] for n in nomes], columns=acc_df.columns)
            pd.concat([acc_df, novos], ignore_index=True).drop_duplicates(subset=['Account']).to_csv('accounts.csv', index=False)
            st.success("Contas cadastradas!")
            st.rerun()
    st.dataframe(acc_df, use_container_width=True)

elif menu == "💸 Lançar Lucro/Perda":
    st.title("Lançar Resultado")
    if acc_df.empty:
        st.error("❌ Erro: Você precisa cadastrar pelo menos uma conta na aba 'Configurar Contas' antes de lançar valores.")
    else:
        with st.form("add_result"):
            acc = st.selectbox("Selecione a Conta", acc_df['Account'].tolist())
            val = st.number_input("Valor do Resultado ($)", step=1.0)
            tipo = st.selectbox("Tipo", ["Profit", "Withdrawal"])
            dat = st.date_input("Data", date.today())
            if st.form_submit_button("Registrar Valor"):
                novo_h = pd.DataFrame([[dat, acc, tipo, val]], columns=hist_df.columns)
                pd.concat([hist_df, novo_h], ignore_index=True).to_csv('history.csv', index=False)
                st.success(f"Registrado: {val} para {acc}")
