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
        try:
            creds = Credentials.from_service_account_file("Projetos Pessoais/credentials.json", scopes=scope)
        except:
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

    if df.empty:
        st.warning("Aguardando dados válidos na planilha.")
    else:
        st.title("📊 Meu Dashboard Financeiro")

        # --- SIDEBAR (FILTROS) ---
        st.sidebar.header("Configurações de Filtro")
        df_meses = df[['Mes_Ano_Exibicao', 'Mes_Ano']].drop_duplicates().sort_values('Mes_Ano', ascending=False)
        lista_exibicao = df_meses['Mes_Ano_Exibicao'].tolist()

        mes_visual = st.sidebar.selectbox("Mês de análise detalhada", lista_exibicao)
        mes_selecionado = df_meses.loc[df_meses['Mes_Ano_Exibicao'] == mes_visual, 'Mes_Ano'].values[0]

        ver_tudo = st.sidebar.checkbox("Visualizar todo o histórico no gráfico", value=False)

        lista_cat = sorted([c for c in df["Categoria"].unique().tolist() if c])
        cat_escolhidas = st.sidebar.multiselect("Filtrar Categorias", lista_cat, default=lista_cat)

        # --- PREPARAÇÃO DOS DADOS ---
        df_mes = df[df['Mes_Ano'] == mes_selecionado]
        df_mes_Receitas = df_mes[df_mes['Valor'] > 0]
        df_mes_saidas = df_mes[df_mes['Valor'] < 0]

        data_referencia = df['Data'].min().replace(day=1)

        if ver_tudo:
            df_para_evolucao = df[df["Categoria"].isin(cat_escolhidas)]
            df_para_investimentos = df
            texto_periodo = "Histórico Total"
            intervalo_ms = 10 * 24 * 60 * 60 * 1000
        else:
            df_para_evolucao = df_mes[df_mes["Categoria"].isin(cat_escolhidas)]
            df_para_investimentos = df_mes
            texto_periodo = mes_visual
            intervalo_ms = 5 * 24 * 60 * 60 * 1000

        # --- MÉTRICAS ---
        Receitas_total = df_mes_Receitas['Valor'].sum()
        saidas_total = df_mes_saidas['Valor'].sum()
        saldo_mensal = Receitas_total + saidas_total

        data_limite = df_mes['Data'].max()
        saldo_acumulado = df[df['Data'] <= data_limite]['Valor'].sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Receitas", f"R$ {Receitas_total:,.2f}")
        m2.metric("Despesas", f"R$ {abs(saidas_total):,.2f}")
        m3.metric("Saldo Mensal", f"R$ {saldo_mensal:,.2f}", delta=f"{saldo_mensal:,.2f}")
        m4.metric("Saldo Acumulado", f"R$ {saldo_acumulado:,.2f}", delta=f"{saldo_acumulado:,.2f}")

        st.divider()

        # --- GRÁFICO 1: EVOLUÇÃO ---
        st.subheader("📈 Evolução Financeira Detalhada")
        df_para_evolucao = df_para_evolucao.copy()
        df_para_evolucao['Status'] = df_para_evolucao['Valor'].apply(lambda x: 'Receitas' if x > 0 else 'Despesas')
        df_plot = df_para_evolucao.groupby(['Data', 'Status', 'Categoria'])['Valor'].sum().reset_index()
        df_plot['Valor_Grafico'] = df_plot['Valor'].abs()

        fig_evolucao = px.line(df_plot, x='Data', y='Valor_Grafico', color='Status', markers=True,
                               color_discrete_map={"Receitas": "#81C784", "Despesas": "#E57373"},
                               category_orders={"Status": ["Receitas", "Despesas"]},
                               template="plotly_dark", custom_data=['Categoria', 'Valor'],
                               labels={"Valor_Grafico": "Valor (R$)", "Data": "Data"})

        fig_evolucao.update_xaxes(tickformat="%d/%m/%Y", dtick=intervalo_ms, tick0=data_referencia, tickmode="linear")
        fig_evolucao.update_layout(hovermode="closest",
                                   legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig_evolucao.update_traces(
            hovertemplate="<b>Data:</b> %{x|%d/%m/%Y}<br><b>Valor Real:</b> R$ %{customdata[1]:,.2f}<br><b>Categoria:</b> %{customdata[0]}<extra></extra>")
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # --- SEÇÃO: EVOLUÇÃO DE INVESTIMENTOS ---
        st.divider()
        st.subheader(f"💰 Evolução de Investimentos ({texto_periodo})")
        total_invest_acumulado = df[df["Categoria"].str.contains("Investimento", case=False, na=False)]["Valor"].sum()
        cor_valor = "#81C784" if total_invest_acumulado >= 0 else "#E57373"
        st.write(
            f'<p style="font-size:16px; font-weight:bold;">Total Investido: <span style="color:{cor_valor};">R$ {total_invest_acumulado:,.2f}</span></p>',
            unsafe_allow_html=True)

        df_invest = df_para_investimentos[
            df_para_investimentos["Categoria"].str.contains("Investimento", case=False, na=False)]
        if not df_invest.empty:
            df_invest_plot = df_invest.groupby(['Data', 'Categoria'])['Valor'].sum().reset_index()
            fig_invest = px.line(df_invest_plot, x='Data', y='Valor', color='Categoria', markers=True,
                                 template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel,
                                 labels={"Valor": "Valor (R$)", "Data": "Data"})
            fig_invest.update_xaxes(tickformat="%d/%m/%Y", dtick=intervalo_ms, tick0=data_referencia, tickmode="linear")
            st.plotly_chart(fig_invest, use_container_width=True)

        # --- SEÇÃO: ANÁLISES MENSAIS ---
        st.divider()
        st.header("🎯 Análises Mensais")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribuição de Gastos")
            df_pizza = df_mes_saidas.copy()
            df_pizza['Valor'] = df_pizza['Valor'].abs()
            if not df_pizza.empty:
                fig_pizza = px.pie(df_pizza, values="Valor", names="Categoria", hole=0.4,
                                   color_discrete_sequence=px.colors.qualitative.Pastel, template="plotly_dark")
                st.plotly_chart(fig_pizza, use_container_width=True)
        with c2:
            st.subheader("Balanço Mensal")
            df_balanco = pd.DataFrame(
                {'Status': ['Receitas', 'Despesas'], 'Total': [Receitas_total, abs(saidas_total)]})
            fig_bar = px.bar(df_balanco, x='Status', y='Total', color='Status',
                             color_discrete_map={"Receitas": "#81C784", "Despesas": "#E57373"})
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- NOVO GRÁFICO: RECORRÊNCIA DOS GASTOS (BARRAS MAIS FINAS) ---
        st.subheader("🔄 Recorrência dos Gastos")
        if not df_mes_saidas.empty:
            df_rec = df_mes_saidas.copy()
            df_rec['Valor_Abs'] = df_rec['Valor'].abs()
            df_rec_plot = df_rec[df_rec['Recorrência'] != 'Receitas'].groupby("Recorrência")[
                "Valor_Abs"].sum().reset_index()

            fig_recorrencia = px.bar(
                df_rec_plot,
                x="Recorrência",
                y="Valor_Abs",
                color="Recorrência",
                template="plotly_dark",
                category_orders={"Recorrência": ["Fixos", "Recorrentes", "Não Recorrentes"]},
                color_discrete_map={
                    "Não Recorrentes": "#E57373",
                    "Recorrentes": "#FFF176",
                    "Fixos": "#64B5F6"
                },
                labels={"Valor_Abs": "Total (R$)"}
            )

            # AJUSTE DA LARGURA: bargap=0.5 deixa as barras mais finas e elegantes
            fig_recorrencia.update_layout(bargap=0.5)

            fig_recorrencia.update_traces(
                hovertemplate="<b>Recorrência:</b> %{x}<br><b>Total:</b> R$ %{y:,.2f}<extra></extra>"
            )
            st.plotly_chart(fig_recorrencia, use_container_width=True)

        # --- RESUMO E LISTA (Final do Código) ---
        st.markdown("### 📋 Resumo de Gastos por Categoria")
        if not df_mes_saidas.empty:
            resumo_cat = df_mes_saidas.groupby("Categoria")["Valor"].sum().abs().reset_index().sort_values(by="Valor",
                                                                                                           ascending=False)
            total_gastos = resumo_cat["Valor"].sum()
            resumo_final = pd.concat([resumo_cat, pd.DataFrame({"Categoria": ["TOTAL"], "Valor": [total_gastos]})],
                                     ignore_index=True)
            st.dataframe(resumo_final.style.format({"Valor": "R$ {:,.2f}"}), use_container_width=True, hide_index=True)

        with st.expander(f"🔍 Lista de lançamentos - {mes_visual}"):
            df_lista = df_mes.iloc[:, :-3].copy()
            df_lista['Data'] = df_lista['Data'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_lista.style.format({"Valor": "R$ {:,.2f}"}), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro crítico: {e}")