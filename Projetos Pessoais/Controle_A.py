import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Controle Financeiro Pessoal")

# --- MAPEAMENTO DOS DADOS (Substitua pelo ID da sua URL) ---
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
def load_data(label_selecionado):
    gid = MAPA_GIDS.get(label_selecionado)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)

    # 1. Identificar coluna de Valor (suporta 'Valor da Parcela' ou 'Valor')
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

    # 2. Identificar coluna de Categoria (suporta 'Categorias' ou 'Categoria')
    col_cat = 'Categorias' if 'Categorias' in df.columns else 'Categoria'

    # 3. Tratamento de Datas
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data']).sort_values('Data', ascending=False)
        # Criamos uma coluna de exibição para os gráficos
        df['Mes_Referencia'] = df['Data'].dt.strftime('%m/%Y')

    return df, col_valor, col_cat


# --- INTERFACE SIDEBAR ---
st.sidebar.title("🔍 Filtros")
selecao_aba = st.sidebar.selectbox("Selecione o Mês/Ano da Planilha", list(MAPA_GIDS.keys()))

try:
    df, nome_col_valor, nome_col_cat = load_data(selecao_aba)

    if df.empty:
        st.warning(f"A aba '{selecao_aba}' parece não ter dados.")
    else:
        # Filtros adicionais na Sidebar
        ver_tudo = st.sidebar.checkbox("Visualizar histórico completo desta aba", value=True)

        lista_cat = sorted(df[nome_col_cat].unique().tolist())
        categorias_selecionadas = st.sidebar.multiselect("Filtrar Categorias", lista_cat, default=lista_cat)

        # Aplicação dos filtros
        df_filtrado = df[df[nome_col_cat].isin(categorias_selecionadas)]

        # --- CORPO DO DASHBOARD ---
        st.title(f"💳 Cartão de Crédito - {selecao_aba}")

        # Métrica Principal
        total_selecionado = df_filtrado[nome_col_valor].sum()
        st.metric(f"Total em {selecao_aba}", f"R$ {total_selecionado:,.2f}")

        # Gráfico de Barras (Histórico da aba atual)
        df_grafico = df_filtrado.groupby('Mes_Referencia')[nome_col_valor].sum().reset_index()
        fig = px.bar(df_grafico, x='Mes_Referencia', y=nome_col_valor,
                     title="Gastos por Período", template="plotly_dark",
                     color_discrete_sequence=["#9b59b6"])
        st.plotly_chart(fig, use_container_width=True)

        # Tabela de Lançamentos Detalhada
        st.markdown("### 📝 Lançamentos Detalhados")
        df_exibicao = df_filtrado[['Data', nome_col_cat, nome_col_valor, 'Descrição (Opcional)']].copy()
        df_exibicao['Data'] = df_exibicao['Data'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_exibicao.style.format({nome_col_valor: "R$ {:.2f}"}), use_container_width=True, hide_index=True)

        # --- RESUMO POR CATEGORIA (COM LINHA VERMELHA) ---
        st.divider()
        st.markdown("### 📋 Resumo de Gastos por Categoria")

        resumo_cat = df_filtrado.groupby(nome_col_cat)[nome_col_valor].sum().reset_index()
        resumo_cat = resumo_cat.sort_values(by=nome_col_valor, ascending=False)

        # Adiciona linha de TOTAL
        total_geral = resumo_cat[nome_col_valor].sum()
        linha_total = pd.DataFrame({nome_col_cat: ["TOTAL"], nome_col_valor: [total_geral]})
        resumo_final = pd.concat([resumo_cat, linha_total], ignore_index=True)


        # Função de estilização para o Total
        def highlight_total(row):
            if row[nome_col_cat] == 'TOTAL':
                return ['background-color: #990000; color: white; font-weight: bold'] * len(row)
            return [''] * len(row)


        st.dataframe(
            resumo_final.style.apply(highlight_total, axis=1)
            .format({nome_col_valor: "R$ {:.2f}"}),
            use_container_width=True, hide_index=True
        )

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.info("Dica: Verifique se a planilha está compartilhada como 'Qualquer pessoa com o link'.")