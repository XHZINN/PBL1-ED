import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modulos.database import conexao_bd

st.set_page_config(page_title="Análise por Bairros", layout="wide")
st.title("📊 Análise de Vulnerabilidade por Bairro - São Luís")
st.markdown("---")

def carregar_dados_bairros():
    """Carrega dados consolidados dos bairros"""
    conn = conexao_bd()
    
    query = """
    WITH familias_com_pessoas AS (
        SELECT 
            f.uuid_bairro,
            f.uuid_familia,
            f.renda_familiar,
            COUNT(p.uuid_pessoa) as qtd_pessoas
        FROM Familias f
        LEFT JOIN Pessoas p ON f.uuid_familia = p.uuid_familia
        GROUP BY f.uuid_familia
    )
    SELECT 
        b.nome_bairro,
        b.nivel_vulnerabilidade as vulnerabilidade_atual,
        COUNT(DISTINCT f.uuid_familia) as total_familias,
        SUM(fcp.qtd_pessoas) as total_pessoas,
        COALESCE(SUM(CASE WHEN p.gestante = 1 THEN 1 ELSE 0 END), 0) as total_gestantes,
        COALESCE(SUM(CASE WHEN p.pcd = 1 THEN 1 ELSE 0 END), 0) as total_pcd,
        AVG(f.renda_familiar) as renda_media_familiar,
        AVG(f.renda_familiar / NULLIF(fcp.qtd_pessoas, 0)) as renda_per_capita_media
    FROM Bairros b
    LEFT JOIN Familias f ON b.uuid_bairro = f.uuid_bairro
    LEFT JOIN familias_com_pessoas fcp ON f.uuid_familia = fcp.uuid_familia
    LEFT JOIN Pessoas p ON f.uuid_familia = p.uuid_familia
    GROUP BY b.uuid_bairro, b.nome_bairro
    ORDER BY b.nivel_vulnerabilidade DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.fillna(0)

def carregar_evolucao_mensal():
    """Carrega dados de evolução mensal por bairro"""
    conn = conexao_bd()
    
    query = """
    SELECT 
        b.nome_bairro,
        strftime('%Y-%m', v.data_visita) as mes,
        COUNT(DISTINCT v.uuid_visita) as total_visitas,
        AVG(v.nivel_vulnerabilidade) as vulnerabilidade_media,
        AVG(v.renda_no_momento) as renda_media,
        SUM(v.auxilio) as total_auxilio
    FROM Visitas v
    JOIN Familias f ON v.uuid_familia = f.uuid_familia
    JOIN Bairros b ON f.uuid_bairro = b.uuid_bairro
    WHERE v.data_visita IS NOT NULL
    GROUP BY b.nome_bairro, strftime('%Y-%m', v.data_visita)
    ORDER BY mes DESC, b.nome_bairro
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def carregar_metricas_gerais():
    """Carrega métricas gerais do sistema"""
    conn = conexao_bd()
    
    query = """
    SELECT 
        COUNT(DISTINCT f.uuid_familia) as total_familias,
        COUNT(DISTINCT p.uuid_pessoa) as total_pessoas,
        AVG(f.nivel_vulnerabilidade) as vulnerabilidade_media_geral,
        COUNT(DISTINCT v.uuid_visita) as total_visitas,
        COUNT(DISTINCT CASE WHEN v.data_visita >= date('now', '-30 days') THEN v.uuid_visita END) as visitas_30d
    FROM Familias f
    LEFT JOIN Pessoas p ON f.uuid_familia = p.uuid_familia
    LEFT JOIN Visitas v ON f.uuid_familia = v.uuid_familia
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.iloc[0] if not df.empty else pd.Series()

# ============================================
# LAYOUT PRINCIPAL COM FILTROS INTEGRADOS
# ============================================

# Carregar dados
with st.spinner("Carregando dados dos bairros..."):
    df_bairros = carregar_dados_bairros()
    df_evolucao = carregar_evolucao_mensal()
    metricas_gerais = carregar_metricas_gerais()

# FILTROS - Barra lateral organizada por categoria
with st.sidebar:
    st.header("🔍 Filtros de Análise")
    
    # Categoria 1: Filtro Geográfico
    st.subheader("📍 Localização")
    
    # Ordenar bairros por vulnerabilidade para melhor experiência
    bairros_ordenados = df_bairros.sort_values('vulnerabilidade_atual', ascending=False)['nome_bairro'].tolist()
    
    tipo_selecao = st.radio(
        "Tipo de seleção:",
        ["Todos os bairros", "Selecionar manualmente", "Top 10 mais críticos", "Top 10 menos críticos"],
        key="tipo_selecao_bairro"
    )
    
    if tipo_selecao == "Todos os bairros":
        bairros_selecionados = bairros_ordenados
    elif tipo_selecao == "Top 10 mais críticos":
        bairros_selecionados = bairros_ordenados[:10]
    elif tipo_selecao == "Top 10 menos críticos":
        bairros_selecionados = bairros_ordenados[-10:]
    else:
        bairros_selecionados = st.multiselect(
            "Selecione os bairros:",
            options=bairros_ordenados,
            default=bairros_ordenados[:3] if len(bairros_ordenados) > 3 else bairros_ordenados
        )
    
    st.markdown("---")
    
    # Categoria 2: Filtro Temporal
    st.subheader("📅 Período de Análise")
    
    if not df_evolucao.empty:
        meses_disponiveis = sorted(df_evolucao['mes'].unique(), reverse=True)
        
        opcao_periodo = st.radio(
            "Período:",
            ["Últimos 3 meses", "Últimos 6 meses", "Último ano", "Personalizado"],
            key="opcao_periodo"
        )
        
        if opcao_periodo == "Últimos 3 meses":
            meses_selecionados = meses_disponiveis[:3]
        elif opcao_periodo == "Últimos 6 meses":
            meses_selecionados = meses_disponiveis[:6]
        elif opcao_periodo == "Último ano":
            meses_selecionados = meses_disponiveis[:12]
        else:
            meses_selecionados = st.multiselect(
                "Selecione os meses:",
                options=meses_disponiveis,
                default=meses_disponiveis[:3] if len(meses_disponiveis) > 3 else meses_disponiveis
            )
    else:
        meses_selecionados = []
        st.warning("Sem dados de evolução mensal")
    
    st.markdown("---")
    
    # Categoria 3: Filtro de Indicadores
    st.subheader("📊 Indicadores")
    
    faixa_vulnerabilidade = st.slider(
        "Faixa de vulnerabilidade:",
        min_value=0.0,
        max_value=10.0,
        value=(0.0, 10.0),
        step=0.5
    )
    
    incluir_sem_familias = st.checkbox("Incluir bairros sem famílias", value=False)
    
    st.markdown("---")
    
    # Botão para atualizar
    atualizar = st.button("🔄 Atualizar Análises", use_container_width=True, type="primary")

# Aplicar filtros
df_bairros_filtrado = df_bairros[
    df_bairros['nome_bairro'].isin(bairros_selecionados) &
    (df_bairros['vulnerabilidade_atual'].between(faixa_vulnerabilidade[0], faixa_vulnerabilidade[1]))
]

if not incluir_sem_familias:
    df_bairros_filtrado = df_bairros_filtrado[df_bairros_filtrado['total_familias'] > 0]

# ============================================
# MÉTRICAS PRINCIPAIS
# ============================================
st.subheader("📌 Visão Geral do Município")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "🏘️ Famílias",
        f"{int(metricas_gerais.get('total_familias', 0)):,}".replace(",", ".")
    )

with col2:
    st.metric(
        "👥 Pessoas",
        f"{int(metricas_gerais.get('total_pessoas', 0)):,}".replace(",", ".")
    )

with col3:
    st.metric(
        "📊 Vulnerab. Média",
        f"{metricas_gerais.get('vulnerabilidade_media_geral', 0):.2f}"
    )

with col4:
    st.metric(
        "📝 Total Visitas",
        f"{int(metricas_gerais.get('total_visitas', 0)):,}".replace(",", ".")
    )

with col5:
    st.metric(
        "📅 Visitas (30d)",
        f"{int(metricas_gerais.get('visitas_30d', 0))}"
    )

st.markdown("---")

# ============================================
# ANÁLISES POR BAIRRO
# ============================================

if not df_bairros_filtrado.empty:
    # Top metrics dos bairros filtrados
    st.subheader(f"📊 Análise dos {len(df_bairros_filtrado)} Bairros Selecionados")
    
    # Cards com informações dos bairros selecionados
    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    
    with col_meta1:
        st.metric(
            "Média Vulnerabilidade",
            f"{df_bairros_filtrado['vulnerabilidade_atual'].mean():.2f}",
            delta=f"{df_bairros_filtrado['vulnerabilidade_atual'].mean() - metricas_gerais.get('vulnerabilidade_media_geral', 0):.2f} vs geral"
        )
    
    with col_meta2:
        st.metric(
            "Total Famílias",
            f"{int(df_bairros_filtrado['total_familias'].sum()):,}".replace(",", ".")
        )
    
    with col_meta3:
        st.metric(
            "Total Pessoas",
            f"{int(df_bairros_filtrado['total_pessoas'].sum()):,}".replace(",", ".")
        )
    
    with col_meta4:
        st.metric(
            "Renda Média Familiar",
            f"R$ {df_bairros_filtrado['renda_media_familiar'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
    
    # Gráficos organizados em abas
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 Ranking de Vulnerabilidade", 
        "📈 Evolução Temporal", 
        "👥 Perfil Demográfico",
        "📋 Tabela Comparativa"
    ])
    
    with tab1:
        col_graf1, col_graf2 = st.columns([2, 1])
        
        with col_graf1:
            # Gráfico de barras horizontal
            df_plot = df_bairros_filtrado.sort_values('vulnerabilidade_atual', ascending=True).tail(15)
            
            fig = px.bar(
                df_plot,
                x='vulnerabilidade_atual',
                y='nome_bairro',
                orientation='h',
                title=f"Ranking de Vulnerabilidade",
                labels={'vulnerabilidade_atual': 'Índice (0-10)', 'nome_bairro': ''},
                color='vulnerabilidade_atual',
                color_continuous_scale='RdYlGn_r',
                range_color=[0, 10],
                text=df_plot['vulnerabilidade_atual'].round(1)
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=500, xaxis_range=[0, 11])
            st.plotly_chart(fig, use_container_width=True)
        
        with col_graf2:
            st.info("""
            ### 🎯 Classificação:
            
            **🔴 Crítico (8-10)**  
            Prioridade máxima para intervenção
            
            **🟠 Alto (6-8)**  
            Necessita atenção especial
            
            **🟡 Médio (3-6)**  
            Monitoramento constante
            
            **🟢 Baixo (0-3)**  
            Situação estável
            """)
            
            # Distribuição por categoria
            categorias = {
                'Crítico (8-10)': len(df_bairros_filtrado[df_bairros_filtrado['vulnerabilidade_atual'] >= 8]),
                'Alto (6-8)': len(df_bairros_filtrado[(df_bairros_filtrado['vulnerabilidade_atual'] >= 6) & (df_bairros_filtrado['vulnerabilidade_atual'] < 8)]),
                'Médio (3-6)': len(df_bairros_filtrado[(df_bairros_filtrado['vulnerabilidade_atual'] >= 3) & (df_bairros_filtrado['vulnerabilidade_atual'] < 6)]),
                'Baixo (0-3)': len(df_bairros_filtrado[df_bairros_filtrado['vulnerabilidade_atual'] < 3])
            }
            
            df_cat = pd.DataFrame(list(categorias.items()), columns=['Categoria', 'Quantidade'])
            
            fig2 = px.pie(
                df_cat,
                values='Quantidade',
                names='Categoria',
                title='Distribuição por Categoria',
                color_discrete_sequence=['#FF4B4B', '#FFA500', '#FFD700', '#90EE90']
            )
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        if not df_evolucao.empty and meses_selecionados:
            df_evol_temp = df_evolucao[
                (df_evolucao['nome_bairro'].isin(bairros_selecionados)) &
                (df_evolucao['mes'].isin(meses_selecionados))
            ]
            
            if not df_evol_temp.empty:
                col_ts1, col_ts2 = st.columns(2)
                
                with col_ts1:
                    # Linha do tempo - Vulnerabilidade
                    fig = px.line(
                        df_evol_temp,
                        x='mes',
                        y='vulnerabilidade_media',
                        color='nome_bairro',
                        markers=True,
                        title="Evolução da Vulnerabilidade",
                        labels={'mes': 'Mês/Ano', 'vulnerabilidade_media': 'Índice Médio', 'nome_bairro': 'Bairro'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col_ts2:
                    # Linha do tempo - Renda Média
                    fig = px.line(
                        df_evol_temp,
                        x='mes',
                        y='renda_media',
                        color='nome_bairro',
                        markers=True,
                        title="Evolução da Renda Média",
                        labels={'mes': 'Mês/Ano', 'renda_media': 'Renda Média (R$)', 'nome_bairro': 'Bairro'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Heatmap de vulnerabilidade por bairro/mês
                st.subheader("🗓️ Mapa de Calor - Vulnerabilidade por Período")
                
                pivot_df = df_evol_temp.pivot_table(
                    values='vulnerabilidade_media',
                    index='nome_bairro',
                    columns='mes',
                    fill_value=0
                )
                
                fig = px.imshow(
                    pivot_df,
                    text_auto='.2f',
                    aspect="auto",
                    color_continuous_scale='RdYlGn_r',
                    title="Intensidade da Vulnerabilidade por Bairro e Mês",
                    labels=dict(x="Mês", y="Bairro", color="Índice")
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.warning("Sem dados de evolução para o período selecionado.")
        else:
            st.info("👈 Selecione um período no menu lateral para visualizar a evolução temporal.")
    
    with tab3:
        col_dem1, col_dem2 = st.columns(2)
        
        with col_dem1:
            # Composição familiar
            fig = px.bar(
                df_bairros_filtrado.sort_values('total_familias', ascending=True).tail(10),
                x='total_familias',
                y='nome_bairro',
                orientation='h',
                title="Top 10 - Total de Famílias por Bairro",
                labels={'total_familias': 'Quantidade', 'nome_bairro': ''},
                color='vulnerabilidade_atual',
                color_continuous_scale='RdYlGn_r'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_dem2:
            # População total
            fig = px.bar(
                df_bairros_filtrado.sort_values('total_pessoas', ascending=True).tail(10),
                x='total_pessoas',
                y='nome_bairro',
                orientation='h',
                title="Top 10 - População por Bairro",
                labels={'total_pessoas': 'Pessoas', 'nome_bairro': ''},
                color='vulnerabilidade_atual',
                color_continuous_scale='RdYlGn_r'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        col_dem3, col_dem4 = st.columns(2)
        
        with col_dem3:
            # Gestantes
            df_gest = df_bairros_filtrado[df_bairros_filtrado['total_gestantes'] > 0].sort_values('total_gestantes', ascending=False).head(10)
            if not df_gest.empty:
                fig = px.pie(
                    df_gest,
                    values='total_gestantes',
                    names='nome_bairro',
                    title="Distribuição de Gestantes por Bairro",
                    hole=0.4
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col_dem4:
            # PCDs
            df_pcd = df_bairros_filtrado[df_bairros_filtrado['total_pcd'] > 0].sort_values('total_pcd', ascending=False).head(10)
            if not df_pcd.empty:
                fig = px.pie(
                    df_pcd,
                    values='total_pcd',
                    names='nome_bairro',
                    title="Distribuição de PCDs por Bairro",
                    hole=0.4
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        # Tabela comparativa completa
        df_display = df_bairros_filtrado.copy()
        df_display = df_display.sort_values('vulnerabilidade_atual', ascending=False)
        
        # Formatação
        df_display['vulnerabilidade_atual'] = df_display['vulnerabilidade_atual'].round(2)
        df_display['renda_media_familiar'] = df_display['renda_media_familiar'].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        df_display['renda_per_capita_media'] = df_display['renda_per_capita_media'].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        
        # Função para colorir linhas por vulnerabilidade
        def colorir_linhas(row):
            try:
                val = float(str(row['vulnerabilidade_atual']).replace(',', '.'))
                if val >= 8:
                    return ['background-color: #FFE5E5'] * len(row)
                elif val >= 6:
                    return ['background-color: #FFF0D9'] * len(row)
                elif val >= 3:
                    return ['background-color: #FFFFE0'] * len(row)
                else:
                    return ['background-color: #E8F5E8'] * len(row)
            except:
                return [''] * len(row)
        
        styled_df = df_display[[
            'nome_bairro', 'vulnerabilidade_atual', 'total_familias', 
            'total_pessoas', 'total_gestantes', 'total_pcd',
            'renda_media_familiar', 'renda_per_capita_media'
        ]].style.apply(colorir_linhas, axis=1)
        
        st.dataframe(
            styled_df,
            column_config={
                "nome_bairro": "Bairro",
                "vulnerabilidade_atual": st.column_config.NumberColumn("Vulnerab.", format="%.2f"),
                "total_familias": "Famílias",
                "total_pessoas": "Pessoas",
                "total_gestantes": "Gestantes",
                "total_pcd": "PCDs",
                "renda_media_familiar": "Renda Média Família",
                "renda_per_capita_media": "Renda per capita"
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Botão de download
        csv = df_bairros_filtrado.to_csv(index=False)
        st.download_button(
            label="📥 Download dos Dados (CSV)",
            data=csv,
            file_name=f"analise_bairros_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

else:
    st.warning("⚠️ Nenhum bairro encontrado com os filtros selecionados.")

st.markdown("---")
st.caption(f"📊 Dados atualizados em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")