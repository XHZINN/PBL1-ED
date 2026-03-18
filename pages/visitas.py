import streamlit as st
from modulos.database import achar_responsavel, achar_familia
from modulos.validacao import validar_tel

st.title("📍 Acompanhamento e Visitas Técnicas")

with st.container(border= True):

    st.write("Buscar familia")
    busca = st.text_input("Nome ou CPF do Responsavel", placeholder="Nome ou CPF", key= "busca_key")

    if busca:
        resultado = achar_responsavel(busca)

        if resultado: 
            def formatar_label(res):
                return f"{res['nome']} - CPF: {res['cpf']} - {res['nome_bairro']}"
            
            escolha = st.selectbox("Selecione a familia encontrada:", options=resultado, format_func=formatar_label)

            if escolha:
                st.success(f"Familia de {escolha['nome']} selecionada")
                st.session_state.familia_focada = escolha

                membros = achar_familia(escolha['uuid_familia'])

                for i, m in enumerate(membros):

                    with st.container(border= True):

                        st.write(m['nome'])

                        if m['sexo'] != "Masculino":
                            c1, c_ges, c_pcd, c2 = st.columns(4)
                        else:
                            c1, c_pcd, c2 = st.columns(3)
                            c_ges = None

                        with c1:
                            m['renda'] = st.number_input("Renda individual", value=m['renda'], key=f"renda_{i}")

                        if c_ges is not None:
                            with c_ges:
                                if m['sexo'] != "Masculino":
                                    
                                    index_gest = 0 if m['gestante'] == 1 else 1 
                                    gestante = st.selectbox("Gestante?", options=["Sim", "Não"], index=index_gest, key=f"gestante_{i}")
                                    m['gestante'] = 1 if gestante == "Sim" else 0

                        with c_pcd:
                            index_pcd = 0 if m['pcd'] == 1 else 1 
                            pcd = st.selectbox("PCD?", options=["Sim", "Não"], index=index_pcd, key=f"pcd_{i}")
                            m['pcd'] = 1 if pcd == "Sim" else 0

                        with c2:
                            telefone = float(m['telefone'] if m["telefone"] is not None else 0.0)
                            m['telefone'] = st.number_input("Telefone" , placeholder="98999999999", value= telefone, on_change=validar_tel, args=(i,), key=f'telefone_{i}')


            else:
                st.warning("Nenhuma familia encontrada com esses dados.")

    

