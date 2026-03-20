import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from modulos.database import carregar_dados_bairros, carregar_evolucao_mensal, pegar_metricas_sistema

st.set_page_config(page_title="Análise por Bairros", layout="wide")
st.title("📊 Análise de Vulnerabilidade por Bairro - São Luís")
st.markdown("---")



# --- LAYOUT PRINCIPAL COM FILTROS INTEGRADOS ---


# Carregar dados
with st.spinner("Carregando dados dos bairros..."):
    df_bairros = carregar_dados_bairros()
    df_evolucao = carregar_evolucao_mensal()
    metricas_gerais = pegar_metricas_sistema()

# FILTROS - Barra lateral organizada por categoria
with st.sidebar:
    st.header("🔍 Filtros de Análise")
    
    
    st.subheader("📍 Localização")
    
    # Ordenar bairros por vulnerabilidade 
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


# --- MÉTRICAS PRINCIPAIS ---

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


# --- ANÁLISES POR BAIRRO ---


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
    tab1, tab2, tab3 = st.tabs([
        "🏆 Ranking de Vulnerabilidade", 
        "📈 Evolução Temporal", 
        "👥 Perfil Demográfico"
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
                title="Ranking de Vulnerabilidade",
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
    
else:
    st.warning("⚠️ Nenhum bairro encontrado com os filtros selecionados.")

st.markdown("---")
st.caption(f"📊 Dados atualizados em: {datetime.now().strftime('%d/%m/%Y')}")