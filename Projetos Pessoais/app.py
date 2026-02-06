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
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    except Exception:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)

    client = gspread.authorize(creds)
    spreadsheet = client.open("Controle Financeiro Mensal com Gráficos")
    sheet = spreadsheet.worksheet("Controle de Gastos")
    df = pd.DataFrame(sheet.get_all_records())

    if 'Valor' in df.columns:
        df['Valor'] = df['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '',
                                                                                             regex=False).str.replace(
            ',', '.', regex=False).str.strip()
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)

    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data']).sort_values('Data')
        df['Mes_Ano'] = df['Data'].dt.strftime('%Y-%m')

    return df


try:
    df = load_data()
    col_tipo = "Tipo (Entrada/Saída)"

    if not df.empty:
        st.title("📊 Meu Dashboard Financeiro")

        # --- SIDEBAR ---
        lista_meses = sorted(df['Mes_Ano'].unique().tolist(), reverse=True)
        mes_sel = st.sidebar.selectbox("Mês de análise", lista_meses)
        df_mes = df[df['Mes_Ano'] == mes_sel]

        # --- MÉTRICAS ---
        ent, sai = df_mes[df_mes[col_tipo] == "ENTRADA"]["Valor"].sum(), df_mes[df_mes[col_tipo] == "SAÍDA"][
            "Valor"].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Entradas", f"R$ {ent:,.2f}")
        m2.metric(f"Saídas", f"R$ {sai:,.2f}")
        m3.metric("Saldo", f"R$ {ent - sai:,.2f}")

        st.divider()

        # --- GRÁFICO DE EVOLUÇÃO (A LÓGICA DA CORREÇÃO) ---
        st.subheader("📈 Evolução Financeira Detalhada")

        # 1. Criamos um resumo para o HOVER (Lista todos os itens do dia)
        hover_summary = df_mes.groupby(['Data', col_tipo]).apply(
            lambda x: "<br>".join([f"• {cat}: R$ {val:,.2f}" for cat, val in zip(x['Categoria'], x['Valor'])])
        ).reset_index(name='detalhes')

        # 2. Criamos o DF para a LINHA (Soma os valores por dia para a linha não quebrar)
        df_linha = df_mes.groupby(['Data', col_tipo])['Valor'].sum().reset_index()

        # 3. Unimos as duas informações
        df_final_plot = pd.merge(df_linha, hover_summary, on=['Data', col_tipo])

        fig = px.line(
            df_final_plot, x='Data', y='Valor', color=col_tipo, markers=True,
            color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"},
            template="plotly_dark",
            custom_data=['detalhes']
        )

        fig.update_traces(
            hovertemplate="<b>Data:</b> %{x|%d/%m/%y}<br><b>Total do Dia:</b> R$ %{y:,.2f}<br><br><b>Categorias:</b><br>%{customdata[0]}<extra></extra>"
        )

        fig.update_layout(
            hovermode="x unified", legend_title_text='', xaxis_title="", yaxis_title="Valor (R$)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # --- GRÁFICOS INFERIORES ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Gastos por Categoria")
            st.plotly_chart(px.pie(df_mes[df_mes[col_tipo] == "SAÍDA"], values="Valor", names="Categoria", hole=0.4),
                            use_container_width=True)
        with c2:
            st.subheader("Entradas vs Saídas")
            st.plotly_chart(px.bar(df_linha, x=col_tipo, y="Valor", color=col_tipo,
                                   color_discrete_map={"ENTRADA": "#2ecc71", "SAÍDA": "#e74c3c"}),
                            use_container_width=True)

except Exception as e:
    st.error(f"Erro: {e}")