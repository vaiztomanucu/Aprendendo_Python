import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Controle Financeiro Real-Time")


# --- FUNÇÃO PARA CARREGAR DADOS ---
@st.cache_data(ttl=60)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]

    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    except Exception:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)

    client = gspread.authorize(creds)
    spreadsheet = client.open("Controle Financeiro Mensal com Gráficos")
    sheet = spreadsheet.worksheet("Controle de Gastos")

    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if 'Valor' in df.columns:
        df['Valor'] = (
            df['Valor']
            .astype(str)
            .str.replace('R$', '', regex=False)
            .str.replace(' ', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)

    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data']).sort_values('Data')
        df['Mes_Ano'] = df['Data'].dt.strftime('%Y-%m')
        df['Mes_Ano_Exibicao'] = df['Data'].dt.strftime('%m/%Y')

    return df


# --- INTERFACE DO DASHBOARD ---
try:
    df = load_data()

    if not df.empty:
        st.title("📊 Meu Dashboard Financeiro")

        # --- SIDEBAR ---
        st.sidebar.header("Configurações de Filtro")
        df_meses = df[['Mes_Ano_Exibicao', 'Mes_Ano']].drop_duplicates().sort_values('Mes_Ano', ascending=False)
        mes_visual = st.sidebar.selectbox("Mês de análise detalhada", df_meses['Mes_Ano_Exibicao'].tolist())
        mes_selecionado = df_meses.loc[df_meses['Mes_Ano_Exibicao'] == mes_visual, 'Mes_Ano'].values[0]
        ver_tudo = st.sidebar.checkbox("Visualizar todo o histórico no gráfico", value=False)
        lista_cat = sorted([c for c in df["Categoria"].unique().tolist() if c])
        cat_escolhidas = st.sidebar.multiselect("Filtrar Categorias", lista_cat, default=lista_cat)

        # --- LÓGICA DE DATAS (AJUSTE SOLICITADO) ---
        # Definimos o ponto zero como o dia 01 do mês mais antigo para alinhar os intervalos
        data_base = df['Data'].min().replace(day=1)

        if ver_tudo:
            df_para_evolucao = df[df["Categoria"].isin(cat_escolhidas)]
            texto_periodo = "Histórico Total"
            # 10 dias em milissegundos para gerar (1, 10, 20, 30)
            intervalo_ms = 10 * 24 * 60 * 60 * 1000
        else:
            df_para_evolucao = df[df['Mes_Ano'] == mes_selecionado]
            df_para_evolucao = df_para_evolucao[df_para_evolucao["Categoria"].isin(cat_escolhidas)]
            texto_periodo = mes_visual
            # 5 dias em milissegundos para gerar (1, 5, 10, 15...)
            intervalo_ms = 5 * 24 * 60 * 60 * 1000

        # --- MÉTRICAS ---
        df_mes = df[df['Mes_Ano'] == mes_selecionado]
        entradas_total = df_mes[df_mes['Valor'] > 0]['Valor'].sum()
        saidas_total = df_mes[df_mes['Valor'] < 0]['Valor'].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Entradas", f"R$ {entradas_total:,.2f}")
        m2.metric("Saídas", f"R$ {abs(saidas_total):,.2f}")
        m3.metric("Saldo Líquido", f"R$ {entradas_total + saidas_total:,.2f}")

        st.divider()

        # --- GRÁFICO 1: EVOLUÇÃO FINANCEIRA ---
        st.subheader("📈 Evolução Financeira Detalhada")
        df_para_evolucao = df_para_evolucao.copy()
        df_para_evolucao['Status'] = df_para_evolucao['Valor'].apply(lambda x: 'ENTRADA' if x > 0 else 'SAÍDA')
        df_plot = df_para_evolucao.groupby(['Data', 'Status', 'Categoria'])['Valor'].sum().reset_index()

        fig_evolucao = px.line(df_plot, x='Data', y=df_plot['Valor'].abs(), color='Status', markers=True,
                               color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"},
                               template="plotly_dark", custom_data=['Categoria', 'Valor'])

        # AJUSTE DO EIXO X (1, 5, 10... ou 1, 10, 20...)
        fig_evolucao.update_xaxes(
            tickformat="%d/%m",
            tickmode="linear",
            tick0=data_base,
            dtick=intervalo_ms
        )

        fig_evolucao.update_traces(
            hovertemplate="<b>Data:</b> %{x|%d/%m/%Y}<br><b>Valor:</b> R$ %{customdata[1]:,.2f}<br><b>Cat:</b> %{customdata[0]}<extra></extra>")
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # --- SEÇÃO: INVESTIMENTOS ---
        st.divider()
        st.subheader(f"💰 Evolução de Investimentos ({texto_periodo})")
        df_invest = df_para_evolucao[df_para_evolucao["Categoria"].str.contains("Investimento", case=False, na=False)]
        if not df_invest.empty:
            fig_invest = px.line(df_invest, x='Data', y='Valor', color='Categoria', markers=True,
                                 template="plotly_dark")
            fig_invest.update_xaxes(tickformat="%d/%m", tickmode="linear", tick0=data_base, dtick=intervalo_ms)
            st.plotly_chart(fig_invest, use_container_width=True)

        # --- SEÇÃO: ANÁLISES MENSAIS ---
        st.divider()
        st.header("🎯 Análises Mensais")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribuição de Gastos")
            df_pizza = df_mes[df_mes['Valor'] < 0].copy()
            fig_pizza = px.pie(df_pizza, values=df_pizza['Valor'].abs(), names="Categoria", hole=0.4)
            fig_pizza.update_traces(hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<extra></extra>")
            st.plotly_chart(fig_pizza, use_container_width=True)
        with c2:
            st.subheader("Balanço")
            df_bar = pd.DataFrame({'Status': ['Entradas', 'Saídas'], 'Total': [entradas_total, abs(saidas_total)]})
            fig_bar = px.bar(df_bar, x='Status', y='Total', color='Status',
                             color_discrete_map={"Entradas": "#2ecc71", "Saídas": "#e74c3c"})
            fig_bar.update_traces(hovertemplate="<b>%{x}</b><br>Total: R$ %{y:,.2f}<extra></extra>")
            st.plotly_chart(fig_bar, use_container_width=True)

except Exception as e:
    st.error(f"Erro: {e}")