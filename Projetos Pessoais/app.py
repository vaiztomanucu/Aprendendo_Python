import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Dashboard Financeiro")


# --- FUNÇÃO PARA CARREGAR DADOS ---
@st.cache_data(ttl=60)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]

    # Tenta carregar as credenciais
    try:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
    except:
        creds = Credentials.from_service_account_file("Projetos Pessoais/credentials.json", scopes=scope)

    client = gspread.authorize(creds)

    # 1. ABRE A PLANILHA PELO NOME
    spreadsheet = client.open("Controle Financeiro Mensal com Gráficos")

    # 2. SELECIONA A ABA EXATA (Baseado na sua imagem image_798fe1.png)
    sheet = spreadsheet.worksheet("Controle de Gastos")

    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # 3. LIMPEZA DOS DADOS (Removendo R$ e convertendo para número)
    # Note que na sua print a coluna chama-se exatamente "Valor"
    if 'Valor' in df.columns:
        df['Valor'] = df['Valor'].astype(str).str.replace('R$', '', regex=False)
        df['Valor'] = df['Valor'].str.replace('.', '', regex=False)
        df['Valor'] = df['Valor'].str.replace(',', '.', regex=False)
        df['Valor'] = pd.to_numeric(df['Valor'].str.strip(), errors='coerce').fillna(0)

    return df


# --- INTERFACE ---
try:
    df = load_data()

    if df.empty:
        st.warning("A aba 'Controle de Gastos' foi encontrada, mas não contém dados.")
    else:
        st.title("📊 Meu Dashboard Financeiro")

        # --- FILTROS NA SIDEBAR ---
        st.sidebar.header("Filtros")

        # Filtro de Categoria (Coluna 'Categoria' na sua planilha)
        lista_categorias = df["Categoria"].unique().tolist()
        # Remove valores vazios da lista de filtros
        lista_categorias = [c for c in lista_categorias if c]

        escolha = st.sidebar.multiselect("Categorias", lista_categorias, default=lista_categorias)
        df_filtrado = df[df["Categoria"].isin(escolha)]

        # --- CARTÕES DE MÉTRICAS ---
        # Usando o nome exato da sua coluna: "Tipo (Entrada/Saída)"
        col_tipo = "Tipo (Entrada/Saída)"

        entradas = df_filtrado[df_filtrado[col_tipo] == "ENTRADA"]["Valor"].sum()
        saidas = df_filtrado[df_filtrado[col_tipo] == "SAÍDA"]["Valor"].sum()
        saldo = entradas - saidas

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", f"R$ {entradas:,.2f}")
        c2.metric("Total Saídas", f"R$ {saidas:,.2f}")
        c3.metric("Saldo Real", f"R$ {saldo:,.2f}")

        # --- GRÁFICOS ---
        col_esq, col_dir = st.columns(2)

        with col_esq:
            st.subheader("Gastos por Categoria")
            fig_pizza = px.pie(df_filtrado[df_filtrado[col_tipo] == "SAÍDA"], values="Valor", names="Categoria",
                               hole=0.4)
            st.plotly_chart(fig_pizza, use_container_width=True)

        with col_dir:
            st.subheader("Entradas vs Saídas")
            fig_bar = px.bar(df_filtrado.groupby(col_tipo)["Valor"].sum().reset_index(),
                             x=col_tipo, y="Valor", color=col_tipo,
                             color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"})
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        st.dataframe(df_filtrado)

except Exception as e:
    st.error(f"Erro detalhado: {e}")
    st.info(
        "Dica: Verifique se os nomes das colunas na Planilha são exatamente: 'Data', 'Categoria', 'Tipo (Entrada/Saída)' e 'Valor'.")