import streamlit as st

st.title ("Cadastro de Familia - São Luís")

if 'membros' not in st.session_state:
    st.session_state.membro = []

def adicionar_membros():

    st.session_state.membro.append({"Nome": "", 'Renda': 0.0, 'Idade': 0})

st.button(' Adicionar Membro', on_click = adicionar_membros())

for i, membro in enumerate(st.session_state.membro):
    with st.container(border= True):
        st.write(f"Membro {i+1}")

        st.session_state.membro[i]['nome'] = st.text_input(f"Nome", key = f'nome_{i}')
        
        st.session_state.membro[i]['Renda'] = st.number_input(f"Renda individual", min_value= 0.0, key = f'renda_{i}')
        
        st.session_state.membro[i]['nome'] = st.number_input(f"Idade", min_value= 0.0, step = 1, key = f'nome_{i}')
        