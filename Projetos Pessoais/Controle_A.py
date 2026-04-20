import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Dashboard Financeiro Pessoal")

# --- MAPEAMENTO DOS DADOS (Substitua pelo seu SHEET_ID real) ---
SHEET_ID = "1qIJAdw_aXcVTBf_ELzb5o2dzD8jjUSeKaCPZ6Hzz1rM"
MAPA_GIDS = {
    "2022": "1031075012",
    "2023": "563253526",
    "2024": "239459010",
    "2025": "1647013799",
    "2026": "45417934"
}


@st.cache_data(ttl=60)
def load_data(ano_selecionado):
    gid = MAPA_GIDS.get(ano_selecionado)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)

    # Tratamento de Valores (Lidando com R$ e formatos brasileiros)
    col_valor = 'Valor da Parcela' if 'Valor da Parcela' in df.columns else 'Valor'
    if col_valor in df.columns:
        df[col_valor] = (
            df[col_valor].astype(str)
            .str.replace('R$', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)

    # Tratamento de Datas
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data']).sort_values('Data', ascending=False)
        df['Mes_Ano'] = df['Data'].dt.strftime('%Y-%m')
        df['Mes_Ano_Exibicao'] = df['Data'].dt.strftime('%m/%Y')

    return df, col_valor


# --- INTERFACE SIDEBAR ---
st.sidebar.title("🔍 Filtros")
ano_escolhido = st.sidebar.selectbox("Selecione o Ano", list(MAPA_GIDS.keys()), index=len(MAPA_GIDS) - 1)

try:
    df, nome_col_valor = load_data(ano_escolhido)

    if df.empty:
        st.warning(f"A aba de {ano_escolhido} não possui dados válidos.")
    else:
        # Filtro de Mês
        st.sidebar.header("Configurações de Filtro")
        df_meses = df[['Mes_Ano_Exibicao', 'Mes_Ano']].drop_duplicates().sort_values('Mes_Ano', ascending=False)
        mes_visual = st.sidebar.selectbox("Mês de análise detalhada", df_meses['Mes_Ano_Exibicao'].tolist())
        mes_referencia = df_meses.loc[df_meses['Mes_Ano_Exibicao'] == mes_visual, 'Mes_Ano'].values[0]

        ver_tudo = st.sidebar.checkbox("Visualizar histórico anual", value=False)

        # Filtro de Categorias
        lista_cat = sorted(df['Categorias'].unique().tolist())
        categorias_selecionadas = st.sidebar.multiselect("Filtrar Categorias", lista_cat, default=lista_cat)

        # --- APLICAÇÃO DOS FILTROS ---
        df_filtrado = df[df['Categorias'].isin(categorias_selecionadas)]
        if not ver_tudo:
            df_mes_detalhe = df_filtrado[df_filtrado['Mes_Ano'] == mes_referencia]
        else:
            df_mes_detalhe = df_filtrado

        # --- ÁREA DO CARTÃO DE CRÉDITO ---
        st.title(f"💳 Área do Cartão de Crédito - {mes_visual}")

        total_mes = df_mes_detalhe[nome_col_valor].sum()
        st.metric(f"Total da Fatura ({mes_visual})", f"R$ {total_mes:,.2f}")

        # Gráfico de Barras Anual
        df_grafico = df_filtrado.groupby('Mes_Ano_Exibicao')[nome_col_valor].sum().reset_index()
        # Ordenar o gráfico cronologicamente (usando Mes_Ano oculto para sorteio)
        df_grafico['Sort'] = pd.to_datetime(df_grafico['Mes_Ano_Exibicao'], format='%m/%Y')
        df_grafico = df_grafico.sort_values('Sort')

        fig = px.bar(df_grafico, x='Mes_Ano_Exibicao', y=nome_col_valor,
                     title="Visão por Fatura", template="plotly_dark",
                     color_discrete_sequence=["#9b59b6"])
        st.plotly_chart(fig, use_container_width=True)

        # Tabela de Lançamentos
        st.markdown(f"**Lançamentos da Fatura de {mes_visual}:**")
        df_lista = df_mes_detalhe[['Data', 'Categorias', nome_col_valor, 'Descrição (Opcional)']].copy()
        df_lista['Data'] = df_lista['Data'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_lista.style.format({nome_col_valor: "R$ {:.2f}"}), use_container_width=True, hide_index=True)

        # --- RESUMO POR CATEGORIA ---
        st.divider()
        st.markdown("### 📋 Resumo de Gastos por Categoria")

        resumo_cat = df_mes_detalhe.groupby("Categorias")[nome_col_valor].sum().reset_index()
        resumo_cat = resumo_cat.sort_values(by=nome_col_valor, ascending=False)

        # Adicionando a linha de TOTAL
        total_geral = resumo_cat[nome_col_valor].sum()
        linha_total = pd.DataFrame({"Categorias": ["TOTAL"], nome_col_valor: [total_geral]})
        resumo_final = pd.concat([resumo_cat, linha_total], ignore_index=True)


        # Função para destacar a linha de total em vermelho
        def highlight_total(row):
            if row['Categorias'] == 'TOTAL':
                return ['background-color: #990000; color: white; font-weight: bold'] * len(row)
            return [''] * len(row)


        st.dataframe(
            resumo_final.style.apply(highlight_total, axis=1)
            .format({nome_col_valor: "R$ {:.2f}"}),
            use_container_width=True, hide_index=True
        )

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")