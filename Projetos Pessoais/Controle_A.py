import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Controle Financeiro Pessoal")

# --- MAPEAMENTO DOS DADOS ---
SHEET_ID = "1k2bdTy3nkQZH3PJn5iU_6-KO1Vn2V7iGolv6FBsrHxA"

MAPA_GIDS = {
    "Abril 2026": "1031075012",
    "Maio 2026": "787735977",
    "Junho 2026": "205575186",
    "Julho 2026": "1203464877",
    "Agosto 2026": "172182624",
    "Setembro 2026": "1465700315",
    "Outubro 2026": "321915309",
    "Novembro 2026": "827479431",
    "Dezembro 2026": "11443059"
}


@st.cache_data(ttl=60)
def load_single_sheet(label_aba):
    gid = MAPA_GIDS.get(label_aba)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)

    # Tratamento de Colunas (Valor e Categoria)
    col_valor = 'Valor da Parcela' if 'Valor da Parcela' in df.columns else 'Valor'
    col_cat = 'Categorias' if 'Categorias' in df.columns else 'Categoria'

    if col_valor in df.columns:
        df[col_valor] = (
            df[col_valor].astype(str)
            .str.replace('R$', '', regex=False).str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False).str.strip()
        )
        df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)

    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df['Mes_Ano'] = df['Data'].dt.strftime('%m/%Y')
        df['Ordem_Mes'] = df['Data'].dt.to_period('M')  # Para ordenar o gráfico corretamente

    return df, col_valor, col_cat


# --- INTERFACE SIDEBAR ---
st.sidebar.title("🔍 Filtros")

anos_disponiveis = sorted(list(set([k.split()[-1] for k in MAPA_GIDS.keys()])), reverse=True)
ano_sel = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)

meses_do_ano = [k.split()[0] for k in MAPA_GIDS.keys() if k.endswith(ano_sel)]
mes_sel = st.sidebar.selectbox("Mês Detalhado (Tabela)", meses_do_ano)

try:
    # 1. CARREGAR TODOS OS MESES DO ANO PARA O GRÁFICO
    lista_dfs_ano = []
    abas_do_ano = [k for k in MAPA_GIDS.keys() if k.endswith(ano_sel)]

    for aba in abas_do_ano:
        temp_df, v_col, c_col = load_single_sheet(aba)
        lista_dfs_ano.append(temp_df)

    df_anual = pd.concat(lista_dfs_ano, ignore_index=True)

    # 2. SEPARAR O MÊS ESPECÍFICO PARA A TABELA E MÉTRICAS
    df_mes_especifico = df_anual[df_anual['Data'].dt.strftime('%B').str.capitalize().isin([mes_sel])]
    # Obs: Se o nome da aba for diferente do nome do mês na data, usamos o filtro pela chave:
    chave_busca = f"{mes_sel} {ano_sel}"
    df_mes_especifico = df_anual[df_anual['Data'].isin(load_single_sheet(chave_busca)[0]['Data'])]  # Garantia de match

    # --- CORPO DO DASHBOARD ---
    st.title(f"📊 Evolução Anual - {ano_sel}")

    # Gráfico de Barras com TODOS os meses do ano selecionado
    df_grafico = df_anual.groupby(['Ordem_Mes', 'Mes_Ano'])[v_col].sum().reset_index()
    df_grafico = df_grafico.sort_values('Ordem_Mes')  # Garante que Janeiro venha antes de Fevereiro, etc.

    fig = px.bar(df_grafico, x='Mes_Ano', y=v_col,
                 title=f"Gastos Totais por Mês em {ano_sel}",
                 labels={'Mes_Ano': 'Mês/Ano', v_col: 'Valor Total (R$)'},
                 template="plotly_dark",
                 color_discrete_sequence=["#9b59b6"])

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- DETALHAMENTO DO MÊS SELECIONADO ---
    st.subheader(f"💳 Detalhes de {mes_sel} {ano_sel}")

    # Filtro de Categorias apenas para os dados do mês
    lista_cat = sorted(df_mes_especifico[c_col].unique().tolist())
    categorias_sel = st.sidebar.multiselect("Filtrar Categorias (Tabela)", lista_cat, default=lista_cat)
    df_filtrado_mes = df_mes_especifico[df_mes_especifico[c_col].isin(categorias_sel)]

    col1, col2 = st.columns(2)
    total_mes = df_filtrado_mes[v_col].sum()
    col1.metric(f"Total {mes_sel}", f"R$ {total_mes:,.2f}")

    # Tabela detalhada
    st.dataframe(
        df_filtrado_mes[['Data', c_col, v_col, 'Descrição (Opcional)']]
        .assign(Data=lambda x: x['Data'].dt.strftime('%d/%m/%Y'))
        .style.format({v_col: "R$ {:.2f}"}),
        use_container_width=True, hide_index=True
    )

    # Resumo por Categoria
    st.markdown("### 📋 Resumo por Categoria")
    resumo_cat = df_filtrado_mes.groupby(c_col)[v_col].sum().reset_index().sort_values(v_col, ascending=False)

    # Adicionar linha de total
    total_geral = resumo_cat[v_col].sum()
    resumo_final = pd.concat([resumo_cat, pd.DataFrame({c_col: ["TOTAL"], v_col: [total_geral]})], ignore_index=True)

    st.dataframe(
        resumo_final.style.apply(
            lambda row: ['background-color: #990000; color: white; font-weight: bold'] * len(row) if row[
                                                                                                         c_col] == 'TOTAL' else [''] * len(
                row), axis=1)
        .format({v_col: "R$ {:.2f}"}),
        use_container_width=True, hide_index=True
    )

except Exception as e:
    st.error(f"Ocorreu um erro: {e}")