import streamlit as st

st.title ("Cadastro de Familia - São Luís")

if 'membros' not in st.session_state:
    st.session_state.membros = []

def adicionar_membros():

    st.session_state.membros.append({"nome": "", 'renda': 0.0, 'idade': 0})

st.button(' Adicionar Membro', on_click = adicionar_membros())

