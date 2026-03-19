import streamlit as st
from modulos.database import achar_responsavel, achar_familia, novo_bairro
from modulos.validacao import validar_tel

st.set_page_config(page_title="Acompanhamento e Visitas Técnicas", layout="wide")
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
<<<<<<< Updated upstream
                id_familia = escolha['uuid_familia']
                st.success(f"Familia de {escolha['nome']} selecionada")
                st.session_state.familia_focada = escolha
=======
                id_f = escolha['uuid_familia']
                
                # Coloca id_familia_atual, membro e familia_focada na memoria do streamlit bem bonitinho
                if 'id_familia_atual' not in st.session_state or st.session_state.id_familia_atual != id_f:
>>>>>>> Stashed changes

                membros = achar_familia(escolha['uuid_familia'])

<<<<<<< Updated upstream
                for i, m in enumerate(membros):
=======
                
                for i, m in enumerate(st.session_state.membro):
                    
                    # Se tiver marca que diz que veio do DB gera um campo pra pessoa do DB
                    if not m.get('is_novo_cadastro', False):
                        with st.container(border=True):
                            st.subheader(f'👤 {m["nome"]}')
                            if m['sexo'] != "Masculino":
                                c_renda, c_pcd, c_ges, c_telefone = st.columns([0.25, 0.25, 0.25, 0.25])
>>>>>>> Stashed changes

                    with st.container(border= True):

                        st.write(m['nome'])

                        if m['sexo'] != "Masculino":
                            c1, c_ges, c_pcd, c2 = st.columns(4)
                        else:
                            c1, c_pcd, c2 = st.columns(3)
                            c_ges = None

<<<<<<< Updated upstream
                        with c1:
                            m['renda'] = st.number_input("Renda individual", value=m['renda'], key=f"renda_{i}")
=======
                            with c_telefone:
                                m['telefone'] = st.text_input("Telefone", value=m['telefone'], key=f"t_ext_{i}")
                    
                    
                    else:
                        # Se não gera uma nova pessoa
                        form(i, m)
>>>>>>> Stashed changes

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
                            m['telefone'] = st.text_input("Telefone" , placeholder="98999999999", value= m['telefone'], on_change=validar_tel, args=(i,), key=f'telefone_{i}')

                with st.container(border=True):

                    st.write("Dados Gerais da familia")

                    # auxilio, bairro 

                    c_aux, c_b, c_bn = st.columns(3)

                    with c_aux:
                        aux = st.selectbox("Recebeu Auxílio?", options=["Sim", "Não"], index=escolha['auxilio'], key=f"aux_{id_familia}")
                        m['auxilio'] = 1 if aux == "Sim" else 0

                    with c_b:
                        bairro_s = st.selectbox("Mudaram de bairro?", options=['Sim', 'Não'], key=f'bairro_{id_familia}')

                    with c_bn:
                        bairro_novo = None
                        if bairro_s == "Sim":
                            bairro_novo = st.text_input("Bairro novo", key=f'bairro_novo_{id_familia}', placeholder='Nome do Bairro')

                    sucesso_bairro_val = st.empty()
                    erro_bairro_val = st.empty()

                    if bairro_s == "Não":
                        m['bairro'] = membros[0]['nome_bairro']

                    else:
                        if not bairro_novo:
                            erro_bairro_val.error("⚠️ Por favor, digite o nome do bairro.")
                            m['bairro'] = membros[0]['nome_bairro']

                        else:
    
                            resultado_bairro = novo_bairro(bairro_novo)

                            if resultado_bairro == "":
                                erro_bairro_val.error(f"⚠️ O local '{bairro_novo}' não foi reconhecido em São Luís.")

                            else:
                                st.session_state.familia_focada['nome_bairro'] = resultado_bairro
                                sucesso_bairro_val.success(f"Bairro {resultado_bairro} validado!")

                    #responsavel, custo moradia

                    c_res, c_res_n = st.columns(2)

                    with c_res:
                        res_select = st.selectbox(f'{escolha['nome']} ainda é o responsavel?', options=['Sim', 'Não'], key=f'responsavel_{id_familia}')
                        
                        with c_res_n:

                            if res_select == "Não":
                                nomes = [m['nome'] for m in membros if m['cpf'] != escolha['cpf_responsavel']]
                                novo_res = st.selectbox("Selecione o novo responsavel",options=nomes, key=f'responsavel_novo_{id_familia}')

                    c_cm, c_tm,c_tm_n = st.columns(3)

                    with c_cm:
                        custo_moradia = st.number_input('Custo moradia',min_value=0.0, value=escolha['custo_moradia'], step=1.0, key=f'custo_moradia_{id_familia}')
                        escolha['custo_moradia'] = custo_moradia

                    with c_tm:
                        tipo_moradia = st.selectbox("Trocou de tipo de moradia?", options=['Sim', 'Não'], key=f'tipo_moradia_{id_familia}')

                        if tipo_moradia == 'Sim':
                            with c_tm_n:
                                todas_moradias = ["Casa Propria", "Cedida", "Aluguel", "Ocupação"]
                                moradia_option = [mor for mor in todas_moradias if mor != escolha['tipo_moradia']]
                                novo_tipo_moradia = st.selectbox("Escolha o novo tipo de moradia", options=moradia_option, key=f'tipo_moradia_novo_{id_familia}')
                                escolha['tipo_moradia'] = novo_tipo_moradia

                    obs = st.text_area('Observação',placeholder="Observação sobre a familia. Ex: familia aparenta viver em condições insalubres...", key='observacao')
<<<<<<< Updated upstream
=======
                    familia['observacao'] = obs

                    st.divider()

                    if st.button("💾 Salvar Visita Técnica", type="primary", use_container_width=True):
                        if bairro_s == "Sim":
                            if st.session_state.familia_focada.get('bairro') == "":
                                st.error("O bairro precisa ser valido antes de salvar")
                        else:
                            with st.spinner("Salvando dados no sistema..."):

                                sucesso = salvar_censo(st.session_state.familia_focada, st.session_state.membro)

                                if sucesso:
                                    st.success("✅ Visita e alterações salvas com sucesso!")
                                    # O uso dos ballons é meramento um alivio mental após esse trabalho todo :)
                                    st.balloons()

>>>>>>> Stashed changes

        else:
            st.warning("Nenhuma familia encontrada com esses dados.")

    

