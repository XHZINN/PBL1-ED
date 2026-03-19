import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from modulos.database import conexao_bd
from modulos.calculos import calcular_idade

st.set_page_config(page_title="Visualizar Famílias", layout="wide")
st.title("👨‍👩‍👧‍👦 Visualização de Famílias Cadastradas")
st.markdown("---")

# --- FUNÇÕES DE AUXÍLIO ---
def formatar_moeda(valor):
    """Formata valores numéricos para o padrão de moeda brasileiro"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def colorir_vulnerabilidade(val):
    """Retorna o estilo CSS baseado no nível de vulnerabilidade"""
    try:
        # Garante que estamos lidando com float
        v = float(val)
        if v >= 8: return 'background-color: #FFE5E5; color: #990000; font-weight: bold' # Crítico
        if v >= 6: return 'background-color: #FFF0D9; color: #995c00' # Alto
        if v >= 3: return 'background-color: #FFFFE0; color: #858500' # Médio
        return 'background-color: #E8F5E8; color: #006600' # Baixo
    except:
        return ''

# --- FUNÇÕES DE DADOS ---
@st.cache_data(ttl=600)
def carregar_todas_familias():
    conn = conexao_bd()
    query = """
    SELECT 
        f.uuid_familia, b.nome_bairro, f.tipo_moradia, f.custo_moradia,
        f.renda_familiar, f.auxilio, f.nivel_vulnerabilidade, f.ultima_visita,
        COUNT(p.uuid_pessoa) as qtd_membros,
        SUM(CASE WHEN p.gestante = 1 THEN 1 ELSE 0 END) as qtd_gestantes,
        SUM(CASE WHEN p.pcd = 1 THEN 1 ELSE 0 END) as qtd_pcd,
        (SELECT nome FROM Pessoas WHERE cpf = f.cpf_responsavel) as nome_responsavel,
        f.cpf_responsavel
    FROM Familias f
    JOIN Bairros b ON f.uuid_bairro = b.uuid_bairro
    LEFT JOIN Pessoas p ON f.uuid_familia = p.uuid_familia
    GROUP BY f.uuid_familia
    ORDER BY f.nivel_vulnerabilidade DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def carregar_membros_familia(uuid_familia):
    conn = conexao_bd()
    query = """
    SELECT nome, sexo, gestante, pcd, renda, data_nasc, telefone, cpf
    FROM Pessoas WHERE uuid_familia = ?
    ORDER BY CASE WHEN cpf = (SELECT cpf_responsavel FROM Familias WHERE uuid_familia = ?) THEN 0 ELSE 1 END, data_nasc
    """
    df = pd.read_sql_query(query, conn, params=(uuid_familia, uuid_familia))
    conn.close()
    if not df.empty:
        df['idade'] = df['data_nasc'].apply(calcular_idade)
        df['faixa_etaria'] = df['idade'].apply(
            lambda x: 'Criança (0-12)' if x < 13 else ('Adolescente (13-17)' if x < 18 else ('Adulto (18-59)' if x < 60 else 'Idoso (60+)'))
        )
    return df

def carregar_estatisticas_gerais():
    conn = conexao_bd()
    query = """
    SELECT 
        COUNT(DISTINCT f.uuid_familia) as total_familias,
        COUNT(p.uuid_pessoa) as total_pessoas,
        AVG(f.nivel_vulnerabilidade) as vulnerabilidade_media,
        AVG(f.renda_familiar) as renda_media,
        COUNT(DISTINCT CASE WHEN f.auxilio = 1 THEN f.uuid_familia END) as familias_com_auxilio
    FROM Familias f
    LEFT JOIN Pessoas p ON f.uuid_familia = p.uuid_familia
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.iloc[0] if not df.empty else pd.Series()

# --- CARREGAMENTO INICIAL ---
df_familias = carregar_todas_familias()
stats_gerais = carregar_estatisticas_gerais()

if df_familias.empty:
    st.warning("Nenhuma família cadastrada.")
    st.stop()

# --- MÉTRICAS ---
st.subheader("📊 Panorama Geral")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("🏘️ Total Famílias", f"{int(stats_gerais['total_familias'])}")
m2.metric("👥 Total Pessoas", f"{int(stats_gerais['total_pessoas'])}")
m3.metric("📊 Vuln. Média", f"{stats_gerais['vulnerabilidade_media']:.2f}")
m4.metric("💰 Renda Média", formatar_moeda(stats_gerais['renda_media']))
taxa = (stats_gerais['familias_com_auxilio'] / stats_gerais['total_familias']) * 100
m5.metric("🆘 Com Auxílio", f"{int(stats_gerais['familias_com_auxilio'])} ({taxa:.1f}%)")

# --- FILTROS SIDEBAR ---
with st.sidebar:
    st.header("🔍 Filtros")
    bairros_sel = st.multiselect("Bairros:", options=sorted(df_familias['nome_bairro'].unique()))
    
    renda_max = float(df_familias['renda_familiar'].max())
    faixa_renda = st.slider("Renda familiar:", 0.0, renda_max, (0.0, renda_max))
    
    tipo_moradia_sel = st.selectbox("Moradia:", ['Todos'] + sorted(df_familias['tipo_moradia'].unique().tolist()))
    
    opcoes_vuln = ['Todas', 'Baixa (0-3)', 'Média (3-6)', 'Alta (6-8)', 'Crítica (8-10)']
    faixa_vuln = st.selectbox("Nível de vulnerabilidade:", opcoes_vuln)

    if st.button("🔄 Resetar Filtros"):
        st.rerun()

# --- LÓGICA DE FILTRAGEM ---
df_filtrado = df_familias.copy()
if bairros_sel:
    df_filtrado = df_filtrado[df_filtrado['nome_bairro'].isin(bairros_sel)]
df_filtrado = df_filtrado[df_filtrado['renda_familiar'].between(faixa_renda[0], faixa_renda[1])]
if tipo_moradia_sel != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['tipo_moradia'] == tipo_moradia_sel]

if faixa_vuln != 'Todas':
    if 'Baixa' in faixa_vuln: df_filtrado = df_filtrado[df_filtrado['nivel_vulnerabilidade'] < 3]
    elif 'Média' in faixa_vuln: df_filtrado = df_filtrado[df_filtrado['nivel_vulnerabilidade'].between(3, 6)]
    elif 'Alta' in faixa_vuln: df_filtrado = df_filtrado[df_filtrado['nivel_vulnerabilidade'].between(6, 8)]
    elif 'Crítica' in faixa_vuln: df_filtrado = df_filtrado[df_filtrado['nivel_vulnerabilidade'] >= 8]

# --- ABAS ---
tab_lista, tab_detalhe, tab_graficos = st.tabs(["📋 Lista", "🔍 Detalhes", "📈 Análise"])

with tab_lista:
    if not df_filtrado.empty:
        # CORREÇÃO DO ERRO: Selecionamos as colunas ANTES de aplicar o Style
        df_view = df_filtrado[[
            'nome_bairro', 'nome_responsavel', 'qtd_membros', 
            'renda_familiar', 'nivel_vulnerabilidade', 'auxilio', 'ultima_visita'
        ]].copy()
        
        # Formatação de texto
        df_view['auxilio'] = df_view['auxilio'].map({1: '✅ Sim', 0: '❌ Não'})
        
        # Aplicação do Style (Aqui ele vira um objeto Styler)
        styled_df = df_view.style.applymap(colorir_vulnerabilidade, subset=['nivel_vulnerabilidade'])
        
        # Exibição
        st.dataframe(
            styled_df,
            column_config={
                "renda_familiar": st.column_config.NumberColumn("Renda", format="R$ %.2f"),
                "nivel_vulnerabilidade": st.column_config.NumberColumn("Vuln.", format="%.2f")
            },
            use_container_width=True, hide_index=True
        )
    else:
        st.warning("Nenhum dado encontrado.")

with tab_detalhe:
    if not df_filtrado.empty:
        escolha = st.selectbox("Selecione uma família:", 
                              options=df_filtrado.index,
                              format_func=lambda x: f"{df_filtrado.loc[x, 'nome_responsavel']} ({df_filtrado.loc[x, 'nome_bairro']})")
        
        f = df_filtrado.loc[escolha]
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Responsável:** {f['nome_responsavel']}")
        c2.write(f"**Renda:** {formatar_moeda(f['renda_familiar'])}")
        c3.write(f"**Membros:** {f['qtd_membros']}")
        
        df_m = carregar_membros_familia(f['uuid_familia'])
        st.table(df_m[['nome', 'sexo', 'idade', 'faixa_etaria', 'cpf']])
    else:
        st.info("Filtre uma família para ver detalhes.")

with tab_graficos:
    if not df_filtrado.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_bar = px.bar(df_filtrado['nome_bairro'].value_counts().reset_index(), 
                            x='nome_bairro', y='count', title="Famílias por Bairro")
            st.plotly_chart(fig_bar, use_container_width=True)
        with col_g2:
            fig_scat = px.scatter(df_filtrado, x='renda_familiar', y='nivel_vulnerabilidade', 
                                 color='nome_bairro', title="Renda vs Vulnerabilidade")
            st.plotly_chart(fig_scat, use_container_width=True)

st.caption(f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")