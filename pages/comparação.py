import streamlit as st
import unicodedata
import time
import pandas as pd
import altair as alt
from modulos.database import todos_responsaveis_familia

def remover_acentos(texto):
    if not texto: return ""
    processado = unicodedata.normalize('NFD', texto)
    return "".join(c for c in processado if unicodedata.category(c) != 'Mn').lower()

def quick_sort_nomes(lista):
    if len(lista) <= 1: return lista
    pivo = lista[len(lista) // 2]
    pivo_limpo = remover_acentos(pivo)
    
    esquerda = [x for x in lista if remover_acentos(x) < pivo_limpo]
    meio     = [x for x in lista if remover_acentos(x) == pivo_limpo]
    direita  = [x for x in lista if remover_acentos(x) > pivo_limpo]
    return quick_sort_nomes(esquerda) + meio + quick_sort_nomes(direita)

def bubble_sort_nomes(lista_original):
    lista = lista_original.copy()
    n = len(lista)
    for i in range(n):
        for j in range(0, n - i - 1):
            if remover_acentos(lista[j]) > remover_acentos(lista[j + 1]):
                lista[j], lista[j + 1] = lista[j + 1], lista[j]
    return lista

def merge_sort_nomes(lista):
    if len(lista) <= 1: return lista
    meio = len(lista) // 2
    esquerda = merge_sort_nomes(lista[:meio])
    direita = merge_sort_nomes(lista[meio:])
    return intercalar(esquerda, direita)

def intercalar(esquerda, direita):
    resultado = []
    i = j = 0
    while i < len(esquerda) and j < len(direita):
        if remover_acentos(esquerda[i]) <= remover_acentos(direita[j]):
            resultado.append(esquerda[i])
            i += 1
        else:
            resultado.append(direita[j])
            j += 1
    resultado.extend(esquerda[i:])
    resultado.extend(direita[j:])
    return resultado

st.set_page_config(page_title="Comparador de Algoritmos", layout="wide")

st.title("📊 Comparação de Performance: Ordenação das famílias")
st.write("Análise de tempo: **Merge Sort** vs **Quick Sort** vs **Bubble Sort**.")
st.write("A análise utiliza os nomes dos responsáveis pelas famílias como base de ordenação.")

if 'responsavel' not in st.session_state:
    st.session_state.responsavel = todos_responsaveis_familia()

responsavel = st.session_state.responsavel
st.info(f"Nomes na base: **{len(responsavel)}**")

if st.button("🚀 Rodar Comparação"):
    s = time.perf_counter()
    res_merge = merge_sort_nomes(responsavel.copy())
    t_merge = time.perf_counter() - s

    s = time.perf_counter()
    res_quick = quick_sort_nomes(responsavel.copy())
    t_quick = time.perf_counter() - s

    s = time.perf_counter()
    res_bubble = bubble_sort_nomes(responsavel.copy())
    t_bubble = time.perf_counter() - s

    c1, c2, c3 = st.columns(3)
    c1.metric("Merge Sort", f"{t_merge:.6f}s")
    c2.metric("Quick Sort", f"{t_quick:.6f}s")
    c3.metric("Bubble Sort", f"{t_bubble:.6f}s", delta=f"{t_bubble/t_quick:.1f}x mais lento", delta_color="inverse")

    st.subheader("Gráfico de Tempo (menor é melhor)")
    df_tempos = pd.DataFrame({
        "Algoritmo": ["Merge", "Quick", "Bubble"],
        "Tempo": [t_merge, t_quick, t_bubble]
    })

    chart = alt.Chart(df_tempos).mark_bar().encode(
        x=alt.X("Algoritmo", sort=["Merge", "Quick", "Bubble"]),
        y=alt.Y("Tempo", title="Tempo (segundos)")
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)

    with st.expander("🔍 Ver amostra da lista ordenada"):
        st.write(res_merge)