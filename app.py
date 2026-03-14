import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="PropDesk Pro", layout="wide")

# Estilo para ficar igual à sua foto
st.markdown("""
    <style>
    .stMetric { background-color: #1e2235; padding: 20px; border-radius: 12px; border: 1px solid #3d4466; }
    div[data-testid="stMetricValue"] > div { color: #00ffcc; }
    .main { background-color: #0e1117; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
def load_data(file, columns):
    if os.path.exists(file):
        df = pd.read_csv(file)
        if 'Date' in df.columns: df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=columns)

acc_df = load_data('accounts.csv', ['Account', 'Group', 'Type_Owner', 'Size', 'Profit_Split'])
hist_df = load_data('history.csv', ['Date', 'Account', 'Type', 'Value'])

# --- MENU ---
menu = st.sidebar.radio("PropDesk Menu", ["📊 Dashboard", "⚙️ Configurar Contas", "💸 Lançar Lucro/Perda"])

if menu == "📊 Dashboard":
    st.title("Dashboard de Contas")
    
    if not acc_df.empty:
        # Filtros
        grupos = acc_df['Group'].unique()
        sel_grupos = st.multiselect("Filtrar por Grupo", grupos, default=grupos)
        
        df_acc_f = acc_df[acc_df['Group'].isin(sel_grupos)]
        cap_total = df_acc_f['Size'].sum()
        total_contas = len(df_acc_f)

        if not hist_df.empty:
            df_m = hist_df.merge(df_acc_f, on='Account', how='inner')
            df_m['Net'] = df_m.apply(lambda x: x['Value'] * (x['Profit_Split']/100) if x['Type_Owner'] == 'Mesa' else x['Value'], axis=1)
            
            lucro_mes = df_m[df_m['Value'] > 0]['Value'].sum()
            perda_mes = df_m[df_m['Value'] < 0]['Value'].sum()
            liquido = df_m['Net'].sum()
        else:
            lucro_mes = perda_mes = liquido = 0

        # CARDS (IGUAL À FOTO)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("CAPITAL TOTAL", f"R$ {cap_total:,.2f}")
        c2.metric("TOTAL CONTAS", f"{total_contas}")
        c3.metric("LUCRO DO MÊS", f"R$ {lucro_mes:,.2f}")
        c4.metric("PERDA DO MÊS", f"R$ {abs(perda_mes):,.2f}", delta_color="inverse")
        c5.metric("RESULTADO LÍQUIDO", f"R$ {liquido:,.2f}")

        # GRÁFICOS
        st.markdown("---")
        if not hist_df.empty:
            st.subheader("📈 Crescimento de Capital (Geral)")
            df_equity = df_m.sort_values('Date').groupby('Date')['Value'].sum().cumsum().reset_index()
            st.plotly_chart(px.area(df_equity, x='Date', y='Value', template="plotly_dark", color_discrete_sequence=['#00ffcc']), use_container_width=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🏆 Ranking de Robôs")
                rank = df_m.groupby('Account')['Value'].sum().reset_index().sort_values('Value', ascending=False)
                st.plotly_chart(px.bar(rank, x='Value', y='Account', orientation='h', color='Value', color_continuous_scale='RdYlGn', template="plotly_dark"), use_container_width=True)
            with col_b:
                st.subheader("🔍 Análise Individual")
                foco = st.selectbox("Escolha um robô", acc_df['Account'].unique())
                df_f = hist_df[hist_df['Account'] == foco].sort_values('Date')
                if not df_f.empty:
                    df_f['Acumulado'] = df_f['Value'].cumsum()
                    st.plotly_chart(px.line(df_f, x='Date', y='Acumulado', template="plotly_dark", markers=True), use_container_width=True)
    else:
        st.info("Nenhuma conta ativa. Vá em 'Configurar Contas'.")

elif menu == "⚙️ Configurar Contas":
    st.title("Configuração de Grupos e Robôs")
    with st.expander("➕ Adicionar Robôs em Massa"):
        g_nome = st.text_input("Nome do Grupo (Ex: Robôs Gold)")
        g_lista = st.text_area("Lista de nomes (um por linha)")
        col1, col2 = st.columns(2)
        g_tipo = col1.selectbox("Tipo", ["Mesa", "Pessoal"])
        g_split = col2.number_input("Seu % (Split)", value=80 if g_tipo == "Mesa" else 100)
        if st.button("Criar Grupo"):
            nomes = [n.strip() for n in g_lista.split('\n') if n.strip()]
            novos = pd.DataFrame([[n, g_nome, g_tipo, 50000, g_split] for n in nomes], columns=acc_df.columns)
            pd.concat([acc_df, novos], ignore_index=True).drop_duplicates(subset=['Account']).to_csv('accounts.csv', index=False)
            st.rerun()
    st.subheader("Suas Contas")
    st.dataframe(acc_df, use_container_width=True)

elif menu == "💸 Lançar Resultados":
    st.title("Lançamento Diário")
    with st.form("lanc"):
        rob = st.selectbox("Selecione o Robô", acc_df['Account'].tolist())
        val = st.number_input("Valor do Dia ($)", step=10.0)
        tipo = st.selectbox("Tipo", ["Profit", "Withdrawal"])
        dat = st.date_input("Data", date.today())
        if st.form_submit_button("Salvar"):
            novo_h = pd.DataFrame([[dat, rob, tipo, val]], columns=hist_df.columns)
            pd.concat([hist_df, novo_h], ignore_index=True).to_csv('history.csv', index=False)
            st.success("Resultado salvo!")
