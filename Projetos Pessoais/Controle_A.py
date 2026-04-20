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

    col_valor = 'Valor da Parcela' if 'Valor da Parcela' in df.columns else 'Valor'
    col_cat = 'Categorias' if 'Categorias' in df.columns else 'Categoria'
    # Identificar coluna de Parcelas
    col_parc = 'Parcelas' if 'Parcelas' in df.columns else 'Parcela'

    if col_valor in df.columns:
        df[col_valor] = (
            df[col_valor].astype(str)
            .str.replace('R$', '', regex=False)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)

    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        meses_pt = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        df['Mes_Nome'] = df['Data'].dt.month.map(meses_pt)
        df['Ordem_Mes'] = df['Data'].dt.to_period('M')

    return df, col_valor, col_cat, col_parc


# --- INTERFACE SIDEBAR ---
st.sidebar.title("🔍 Filtros")

anos_disponiveis = sorted(list(set([k.split()[-1] for k in MAPA_GIDS.keys()])), reverse=True)
ano_sel = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)

meses_do_ano = [k.split()[0] for k in MAPA_GIDS.keys() if k.endswith(ano_sel)]
mes_sel = st.sidebar.selectbox("Mês Detalhado (Tabela)", meses_do_ano)

try:
    lista_dfs_ano = []
    abas_do_ano = [k for k in MAPA_GIDS.keys() if k.endswith(ano_sel)]

    for aba in abas_do_ano:
        temp_df, v_col, c_col, p_col = load_single_sheet(aba)
        lista_dfs_ano.append(temp_df)

    df_anual = pd.concat(lista_dfs_ano, ignore_index=True)
    df_mes_especifico = df_anual[df_anual['Mes_Nome'] == mes_sel]

    # --- CORPO DO DASHBOARD ---
    st.title(f"📊 Evolução Anual - {ano_sel}")

    # Filtro de Crédito (Exclui Luz e Água via busca parcial para evitar erro de emoji/espaço)
    df_para_grafico = df_anual[~df_anual[c_col].str.contains("Água|Luz", case=False, na=False)]

    df_grafico = df_para_grafico.groupby(['Ordem_Mes', 'Mes_Nome'])[v_col].sum().reset_index()
    df_grafico = df_grafico.sort_values('Ordem_Mes')

    fig = px.bar(df_grafico, x='Mes_Nome', y=v_col,
                 title=f"Gastos Totais no Crédito por Mês em {ano_sel}",
                 template="plotly_dark", color_discrete_sequence=["#9b59b6"])

    fig.update_traces(hovertemplate="<b>Mês:</b> %{x}<br><b>Valor Total:</b> R$ %{y:,.2f}<extra></extra>")
    fig.update_layout(xaxis_title=None, yaxis_title="Valor Total (R$)")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- DETALHAMENTO DO MÊS SELECIONADO ---
    st.subheader(f"💳 Detalhes de {mes_sel} {ano_sel}")

    lista_cat = sorted(df_mes_especifico[c_col].unique().tolist())
    categorias_sel = st.sidebar.multiselect("Filtrar Categorias (Tabela)", lista_cat, default=lista_cat)
    df_filtrado_mes = df_mes_especifico[df_mes_especifico[c_col].isin(categorias_sel)]

    # Filtro para a Tabela (Exclui Luz e Água)
    df_tabela_final = df_filtrado_mes[~df_filtrado_mes[c_col].str.contains("Água|Luz", case=False, na=False)]

    total_mes_tabela = df_tabela_final[v_col].sum()
    col1, _ = st.columns(2)
    col1.metric(f"Total Fatura {mes_sel}", f"R$ {total_mes_tabela:,.2f}")

    st.markdown("**Lançamentos Detalhados (Apenas Crédito):**")

    # Adicionada a coluna p_col (Parcelas) na lista de exibição
    colunas_exibir = ['Data', c_col, p_col, v_col, 'Descrição (Opcional)']

    st.dataframe(
        df_tabela_final[colunas_exibir]
        .assign(Data=lambda x: x['Data'].dt.strftime('%d/%m/%Y'))
        .style.format({v_col: "R$ {:.2f}"}),
        use_container_width=True, hide_index=True
    )

    # --- RESUMO POR CATEGORIA ---
    st.divider()
    st.markdown(f"### 📋 Resumo de Gastos por Categoria - {mes_sel}")

    resumo_cat = df_filtrado_mes.groupby(c_col)[v_col].sum().reset_index().sort_values(v_col, ascending=False)
    total_geral_resumo = resumo_cat[v_col].sum()
    resumo_final = pd.concat([resumo_cat, pd.DataFrame({c_col: ["TOTAL"], v_col: [total_geral_resumo]})],
                             ignore_index=True)


    def highlight_total(row):
        if row[c_col] == 'TOTAL':
            return ['background-color: #990000; color: white; font-weight: bold'] * len(row)
        return [''] * len(row)


    st.dataframe(
        resumo_final.style.apply(highlight_total, axis=1)
        .format({v_col: "R$ {:.2f}"}),
        use_container_width=True, hide_index=True
    )

except Exception as e:
    st.error(f"Erro ao processar dados: {e}")