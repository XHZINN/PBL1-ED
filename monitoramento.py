#==== IMPORTAÇÕES ====
import streamlit as st 
import pandas as pd 
import folium 
from folium.plugins import HeatMap
from datetime import datetime
from streamlit_folium import st_folium
import plotly.express as px # biblio para os gráficos
from modulos.relatorio import gerar_relatorio
from modulos.database import pegar_totais, bairros_query, criar_table
import os

criar_table()

# config da página (o titulozinho la em cima e o tamanho do layout)
st.set_page_config(page_title="Monitoramento SLZ", layout="wide")

dados_bairros = bairros_query()
    
df = pd.DataFrame(dados_bairros)

st.sidebar.header("Filtros")
nivel_minimo = st.sidebar.slider("Filtrar por Intensidade Mínima", 0.0, 10.0, 0.0)

df = df[df['intensidade'] >= nivel_minimo]

st.sidebar.divider()
st.sidebar.header("Relatório")

nome_pdf = f'Relatorio_Sao_Luis_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'

imagens_temporarias = ['panorama_geral.png', 'top_criticos.png']


if st.sidebar.button("📄 Gerar Relatório PDF"):
    with st.sidebar.status("Processando...", expanded=False):
        gerar_relatorio()
        st.sidebar.success("Relatório pronto!")
if os.path.exists(nome_pdf):
    with open(nome_pdf, "rb") as f:
        pdf_byte_data = f.read()
    try:
        os.remove(nome_pdf)
        for img in imagens_temporarias:
            if os.path.exists(img):
                os.remove(img)
    except Exception as e:
        print(f"Erro ao limpar arquivos: {e}")
    st.sidebar.download_button(
        label="📥 Baixar relatório PDF",
        data=pdf_byte_data,
        file_name="Relatorio_Vulnerabilidade_SLZ.pdf",
        mime="application/pdf"
    )
else:
    st.sidebar.info("Gere o relatório para habilitar o download.")

m = folium.Map(
    location=[-2.550, -44.270], 
    zoom_start=12, 
    tiles="CartoDB dark_matter",
    control_scale=True,
)

heat_data = [[row['lat'], row['lon'], row['intensidade']] for index, row in df.iterrows()]

HeatMap(
    heat_data, 
    radius=35, 
    blur=20, 
    min_opacity=0.3,
    gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 1: 'red'}
).add_to(m)

def pegar_cor(intensidade):
    if intensidade >= 9.0:
        return "#FF0000"
    elif intensidade >= 7.0:
        return "#FFA500"
    elif intensidade >= 5.0:
        return "#FFFB00"
    else:
        return "#00CCFF"

for index, row in df.iterrows():

    cor_bairro = pegar_cor(row['intensidade'])

    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=15,
        color='transparent',
        fill=True,
        fill_color='transparent',
        fill_opacity=0,
        popup=folium.Popup(f"""
            <div style="
                font-family: sans-serif; 
                background-color: {cor_bairro}; 
                color: {'black' if row['intensidade'] < 9.0 else 'white'}; 
                padding: 10px; 
                border-radius: 5px;
                width: 150px;
            ">
                <strong style="display: block; margin-bottom: 5px;">{row['bairro']}</strong>
                <span>Risco: {row['intensidade']}</span>
            </div>
        """, max_width=200)
    ).add_to(m)

col_esq, col_meio, col_dir = st.columns([1, 5, 1])

with col_meio:
    st.title("Monitoramento de Áreas de Risco – São Luís/MA")
    st_folium(m, use_container_width=True, height=500)

st.write("---")

st.header("Detalhamento das Zonas de Alerta")

if not df.empty:

    m1, m2, m3 = st.columns(3)
    maior_risco = df['intensidade'].max()
    bairro_critico = df.loc[df['intensidade'].idxmax(), 'bairro']

    m1.metric("Total de Áreas", len(df))
    m2.metric("Maior Intensidade", f"{maior_risco:.2f}")
    m3.metric("Bairro Crítico", bairro_critico)

    col_tabela_esq, col_tabela_meio, col_tabela_dir = st.columns([1, 3, 1])

    with col_tabela_meio:
        tabela_base = df[['bairro', 'intensidade']].sort_values(by='intensidade', ascending=False)

        tabela_estilizada = tabela_base.style.background_gradient(
            cmap='YlOrRd',
            subset=['intensidade']
        ).format(precision=2)

        st.dataframe(
            tabela_estilizada, 
            use_container_width=True, 
            hide_index=True
        )

    totais = pegar_totais()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="Total de Familias", value=int(totais[0]))

    with col2:
        st.metric(label="Total de Pessoas Residentes", value=int(totais[1]))

    st.divider()

    st.write("### Análise Estatística por Bairro")
    graf_col1, graf_col2 = st.columns(2)

    with graf_col1:
        
        fig_barras = px.bar( 
            df, 
            x='bairro',
            y='intensidade',
            title="Nível de Intensidade por Bairro",
            labels={'intensidade': 'Intensidade', 'bairro': 'Bairro'},
            color='intensidade',
            color_continuous_scale='YlOrRd'
        )
        st.plotly_chart(fig_barras, use_container_width=True) 

    with graf_col2:
    
        fig_rosca = px.pie(
            df, 
            values='intensidade', 
            names='bairro', 
            title="Distribuição Relativa de Risco",
            hole=0.4
        )
        st.plotly_chart(fig_rosca, use_container_width=True)
else:
    st.warning("Nenhum bairro encontrado com essa intensidade. Tente diminuir o filtro na barra lateral.")

st.write("---")
st.caption(f"📊 Dados atualizados em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.caption("Fonte: Defesa Cívil (Simulação para fins acadêmicos)")