#==== IMPORTAÇÕES ====
import streamlit as st # interface do site
import pandas as pd # organizar os dados em tabelas(DataFrames)
import json # arquivos json
import folium # pra criar o mapa
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import plotly.express as px # biblio para os gráficos
from modulos.database import pegar_totais, bairros_query

# config da página (o titulozinho la em cima e o tamanho do layout)
st.set_page_config(page_title="Monitoramento SLZ", layout="wide")

# #==== .JSON ====
# # 1. abrir o arquivo em modo de leitura (r = read)
# with open('bairros.json', 'r', encoding='utf-8') as arquivo:
#     # 2. O json.load transforma o texto do arquivo em uma lista/dicionário Python
#     dados_bairros = json.load(arquivo)
#     # Criar um controle na barra lateral

dados_bairros = bairros_query()
    
# transforma a lista de dicionários em uma tabela do Pandas (DataFrame)
df = pd.DataFrame(dados_bairros)

#==== FILTRO DE INTENSIDADE ====
#MT MASSA ESSA PARTE
# criamos um controle na barra lateral
st.sidebar.header("Filtros")
nivel_minimo = st.sidebar.slider("Filtrar por Intensidade Mínima", 0.0, 1.0, 0.0)
# aqui a gente tá filtrando o DataFrame antes de criar o mapa e a tabela
df = df[df['intensidade'] >= nivel_minimo]

#==== CONFIGURAÇÃO DO MAPA ====

# centralizar o mapa em São Luís (latitude e longitude médias)
# zoom_start=12 distância para ver a ilha toda
m = folium.Map(
    location=[-2.550, -44.270], 
    zoom_start=12, 
    tiles="CartoDB dark_matter", # deixa em modo escuro
    control_scale=True,
)

# Criamos uma lista só com os números que o HeatMap precisa
# Para cada linha (row) da nossa tabela (df), pegamos lat, lon e intensidade
heat_data = [[row['lat'], row['lon'], row['intensidade']] for index, row in df.iterrows()]

# Adicionamos a camada de calor ao mapa 'm'
HeatMap(
    heat_data, 
    radius=35, 
    blur=20, 
    min_opacity=0.3,
    gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 1: 'red'} # do frio ao quente, tipo degradê
).add_to(m)

#==== CLICAR NO MAPA DE CALOR ====

# vamo fazer as cores do popup terem as cores da intensidade
def pegar_cor(intensidade):
    if intensidade >= 0.9:
        return "#FF0000"
    elif intensidade >= 0.7:
        return "#FFA500"
    elif intensidade >= 0.5:
        return "#FFFB00"
    else:
        return "#00CCFF"
# loop pra analizar as tabelas do DF(analogicamente é como se fosse analisar cada linha do JSON)

# ele vai usar os dados de onde estão os bairros pra poder criar
#um botão clicável que vai aparecer o nome e intensidade do bairro
for index, row in df.iterrows():

    cor_bairro = pegar_cor(row['intensidade'])

    folium.CircleMarker(
        #aqui pega as coordenadas
        location=[row['lat'], row['lon']],
        #tamanho da área que aceita o clique
        radius=15,
        #ele existe mas é invisível
        color='transparent',
        fill=True,
        fill_color='transparent',
        fill_opacity=0,
        # essa parte precisei de ajuda pra colocar o CSS
        popup=folium.Popup(f"""
            <div style="
                font-family: sans-serif; 
                background-color: {cor_bairro}; 
                color: {'black' if row['intensidade'] < 0.9 else 'white'}; 
                padding: 10px; 
                border-radius: 5px;
                width: 150px;
            ">
                <strong style="display: block; margin-bottom: 5px;">{row['bairro']}</strong>
                <span>Risco: {row['intensidade']}</span>
            </div>
        """, max_width=200)
    ).add_to(m)





#==== CONFIG DA PRIMEIRA PARTE ====
# gambiarrinha pra centralizar: criamos 3 colunas (laterais pequenas e meio grande)
col_esq, col_meio, col_dir = st.columns([1, 5, 1])

# o 'with' diz: "Python, tudo que tiver esse espacinho (indentação) aqui embaixo, joga na coluna do meio"
with col_meio:
    # O use_container_width=True faz o mapa esticar até o limite da coluna
    st.title("Monitoramento de Áreas de Risco – São Luís/MA")
    st_folium(m, use_container_width=True, height=500)

#linhazinha só pra separar
st.write("---")

#==== PARTE DO DETALHAMENTO E MAPA ====
st.header("Detalhamento das Zonas de Alerta")

# aqui a gente vai botar um resumo rápido, umas métricas pra aparecer no começo

m1, m2, m3 = st.columns(3)
maior_risco = df['intensidade'].max()
bairro_critico = df.loc[df['intensidade'].idxmax(), 'bairro']

m1.metric("Total de Áreas", len(df))
m2.metric("Maior Intensidade", f"{maior_risco:.2f}")
m3.metric("Bairro Crítico", bairro_critico)

#==== TABELA ====

# Criamos outra "gambiarrinha" de colunas pra tabela não ficar esticada demais na tela toda
col_tabela_esq, col_tabela_meio, col_tabela_dir = st.columns([1, 3, 1])

with col_tabela_meio:
    # criamos apenas com as colunas que interessam e ordenamos pela intensidade
    tabela_base = df[['bairro', 'intensidade']].sort_values(by='intensidade', ascending=False)

    # aqui a gente cria o estilo do fundo colorido
    # cmap='YlOrRd' significa Yellow-Orange-Red (Amarelo-Laranja-Vermelho)
    tabela_estilizada = tabela_base.style.background_gradient(
        cmap='YlOrRd',
        subset=['intensidade']
    ).format(precision=2)

    st.dataframe(
        tabela_estilizada, 
        use_container_width=True, 
        hide_index=True # esconde a coluna de index
    )

totais = pegar_totais()

col1, col2 = st.columns(2)

with col1:
    st.metric(label="Total de Familias", value=int(totais[0]))

with col2:
    st.metric(label="Total de Pessoas Residentes", value=int(totais[1]))

st.divider()

#=== GRÁFICOS ===

st.write("### Análise Estatística por Bairro")
# vamos usar a tática de dividir a página em colunas de novo 
graf_col1, graf_col2 = st.columns(2)

with graf_col1: # 1° gráfico: de Barras)
    
    fig_barras = px.bar( #guardamos na variável o gráfico de barras (a função px.bar)
        df, # o primeiro argumento é a fonte dos dados 
        x='bairro', # pega o bairro e usa no eixo x
        y='intensidade', # pega a intensidade e usa no eixo y
        title="Nível de Intensidade por Bairro", # título né
        #esse aqui serve pra mostrar de forma diferente do BD, se tipo, no BD estivesse
        #intensidade_risco_calcular ai ele mostraria o que tá dps dos 2 pontos
        # {'Nome_Original': 'Nome_Para_Exibir'}
        labels={'intensidade': 'Intensidade', 'bairro': 'Bairro'},
        color='intensidade', # muda a cor com base na intensidade
        color_continuous_scale='YlOrRd' # a mesma escala da tabela também
    )
    st.plotly_chart(fig_barras, use_container_width=True) 
    # use_container_width=True é pra ocupar toda a largura da coluna (responsividade)
    #o px.bar só cria a tabela, mas é esse comando de cima que realmente mostra o gráfico

with graf_col2: # 2° gráfico: de Torta 
 
    fig_rosca = px.pie(
        df, 
        values='intensidade', 
        names='bairro', 
        title="Distribuição Relativa de Risco",
        hole=0.4 # faz o buraco no meio
    )
    st.plotly_chart(fig_rosca, use_container_width=True)

st.divider()

st.write("Dados lidos em tempo real do arquivo: `Banco_dados.db`")

st.write("---")
st.caption("Última atualização dos dados: 22 de Fevereiro de 2026")
st.caption("Fonte: Defesa Cívil (Simulação para fins acadêmicos)")