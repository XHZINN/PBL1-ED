import streamlit as st
from datetime import date, timedelta
from modulos.database import achar_responsavel, achar_familia, novo_bairro, salvar_censo
from modulos.validacao import validar_tel, validar_cpf, validar_data, validar_nome
from modulos.calculos import calcular_idade

st.title("📍 Acompanhamento e Visitas Técnicas")

# --- DEF AUXILIO ---

def adicionar_membro(uuid_familia):
    if len(st.session_state.membro) > 0:
        ultimo = st.session_state.membro[-1]
        if not ultimo.get("nome", "").strip() and not ultimo.get('cpf', "").strip():
            st.toast("Preencha o nome do membro atual antes de adicionar outro!", icon="🚫")
            return

    st.session_state.membro.append({
        "nome": "", "erro_nome": "","cpf": "","erro_cpf": "",
        "sexo": "Masculino", 'renda': 0.0,
        "gestante": 0, "pcd": 0, 'erro_data': "",
        'data_nasc': date.today(), "telefone": "", 
        "erro_tel": "", "uuid_familia": uuid_familia,
        "is_novo_cadastro": True 
    })

def remover_membro(indice):
    st.session_state.membro.pop(indice) 

def form(i, membro):
    """Formulário completo para quem está sendo cadastrado agora"""
    with st.container(border=True):
        c_header, c_trash = st.columns([0.8, 0.2])
        with c_header:
            st.write(f'📝 **Cadastrando Novo Membro {i + 1}**')
        with c_trash:
            st.button("❌", key=f"btn_excluir_{i}", on_click=remover_membro, args=(i,))

        c_nome, c_cpf, c_pcd = st.columns(3)
        with c_nome:
            membro['nome'] = st.text_input("Nome", value=membro['nome'], on_change=validar_nome, args=(i, True), key=f'nome_novo_{i}')
            if membro.get('erro_nome'):
                st.error(membro['erro_nome'])
        
        with c_cpf:
            membro['cpf'] = st.text_input("CPF", value=membro['cpf'],on_change=validar_cpf, args=(i, True), max_chars=11, key=f'cpf_novo_{i}')
            if membro.get('erro_cpf'):
                    st.error(membro['erro_cpf'])
        
        with c_pcd:
            pcd_op = ["Não", "Sim"]
            pcd_idx = 1 if membro['pcd'] == 1 else 0
            pcd_select = st.selectbox("PCD", options=pcd_op, index=pcd_idx, key=f'pcd_novo_{i}')
            membro['pcd'] = 1 if pcd_select == "Sim" else 0

        c_renda, c_data, c_tel = st.columns(3)
        with c_renda:
            membro['renda'] = st.number_input("Renda", value=float(membro['renda']), key=f'renda_novo_{i}')
        with c_data:
            date_min = date.today() - timedelta(days=43800)
            membro['data_nasc'] = st.date_input("Nascimento",on_change=validar_data, args=(i, True), max_value=date.today(), min_value=date_min, value=membro['data_nasc'], key=f'data_novo_{i}')
            if membro.get('erro_data'):
                st.error(membro['erro_data'])
        
        with c_tel:
            membro['telefone'] = st.text_input("Telefone", value=membro['telefone'], on_change=validar_tel, args=(i, True), key=f'tel_novo_{i}')
            if membro.get('erro_tel'):
                st.error(membro['erro_tel'])
        c_sexo, c_ges = st.columns(2)

        with c_sexo:
            sexo_select = st.selectbox("Sexo Biológico / Gênero", options=["Masculino", "Feminino", "Não-binário", "Prefiro não informar"], key=f'sexo_n_{i}')
            membro['sexo'] = sexo_select

        if sexo_select != "Masculino":
            with c_ges:
                gest_select = st.selectbox("Gestante", options=["Não", "Sim"], key=f'gestante_novo_{i}')
                membro['gestante'] = 1 if gest_select == "Sim" else 0

# --- INTERFACE PRINCIPAL ---

with st.container(border=True):
    st.write("### 🔍 Buscar Família")
    busca = st.text_input("Nome ou CPF do Responsável", placeholder="Digite para buscar...", key="busca_key")

    if busca:
        resultado = achar_responsavel(busca)
        if resultado:
            def formatar_label(res):
                return f"{res['nome']} - CPF: {res['cpf']} - {res['nome_bairro']}"
            
            escolha = st.selectbox("Selecione a família:", options=resultado, format_func=formatar_label)

            if escolha:
                id_f = escolha['uuid_familia']
                
                # Inicialização da sessão de membros
                if 'id_familia_atual' not in st.session_state or st.session_state.id_familia_atual != id_f:

                    st.session_state.familia_focada = escolha.copy()
                    dados = achar_familia(id_f)
                    # Se vier do banco de dados recebe uma chave nova dizendo que não é um MEMBRO novo
                    for d in dados: 
                        d['is_novo_cadastro'] = False
                    st.session_state.membro = dados
                    st.session_state.id_familia_atual = id_f
                    membros = st.session_state.membro

                
                for i, m in enumerate(st.session_state.membro):
                    
                    
                    if not m.get('is_novo_cadastro', False):
                        with st.container(border=True):
                            st.subheader(f'👤 {m["nome"]}')
                            if m['sexo'] != "Masculino":
                                c_renda, c_pcd, c_ges, c_telefone = st.columns([0.25, 0.25, 0.25, 0.25])

                            else:
                                c_renda, c_pcd, c_telefone = st.columns([0.33, 0.33, 0.33])
                            
                            with c_renda:
                                m['renda'] = st.number_input("Renda", value=float(m['renda']), key=f"r_ext_{i}")
                            
                            pcd_idx = 0 if m['pcd'] == 1 else 1

                            with c_pcd:
                                pcd_val = st.selectbox("PCD?", ["Sim", "Não"], index=pcd_idx, key=f"p_ext_{i}")
                                m['pcd'] = 1 if pcd_val == "Sim" else 0

                            ges_idx = 0 if m['gestante'] == 1 else 1
                            if m['sexo'] != "Masculino":
                                with c_ges:
                                    ges_val = st.selectbox("Gestante?", ["Sim", "Não"], index=ges_idx, key=f"g_ext_{i}")
                                    m['gestante'] = 1 if ges_val == "Sim" else 0

                            with c_telefone:
                                m['telefone'] = st.text_input("Telefone", value=m['telefone'], key=f"t_ext_{i}")
                    
                    
                    else:
                        form(i, m)

                st.divider()
                st.button("➕ Adicionar Membro", on_click=adicionar_membro, args=(id_f,))

                # --- DADOS GERAIS DA FAMÍLIA ---
                with st.container(border=True):
                    nomes = None
                    familia = st.session_state.familia_focada

                    st.write("Dados Gerais da familia")

                    c_aux, c_b, c_bn = st.columns(3)

                    with c_aux:
                        aux = st.selectbox("Recebeu Auxílio?", options=["Sim", "Não"], key=f"aux_{id_f}")
                        familia['auxilio'] = 1 if aux == "Sim" else 0

                    with c_b:
                        bairro_s = st.selectbox("Mudaram de bairro?", options=['Sim', 'Não'], key=f'bairro_{id_f}')

                    with c_bn:
                        bairro_novo = None
                        if bairro_s == "Sim":
                            bairro_novo = st.text_input("Bairro novo", key=f'bairro_novo_{id_f}', placeholder='Nome do Bairro')

                    sucesso_bairro_val = st.empty()
                    erro_bairro_val = st.empty()

                    if bairro_s == "Não":
                        familia['bairro'] = familia['nome_bairro']

                    else:
                        if not bairro_novo:
                            erro_bairro_val.error("⚠️ Por favor, digite o nome do bairro.")
                            familia['bairro'] = familia['nome_bairro']

                        else:
    
                            resultado_bairro = novo_bairro(bairro_novo)

                            if resultado_bairro == "":
                                erro_bairro_val.error(f"⚠️ O local '{bairro_novo}' não foi reconhecido em São Luís.")

                            else:
                                familia['nome_bairro'] = resultado_bairro
                                sucesso_bairro_val.success(f"Bairro {resultado_bairro} validado!")
                    if len(st.session_state.membro) > 1:
                        c_res, c_res_n = st.columns(2)

                        with c_res:
                            res_select = st.selectbox(f'{escolha['nome']} ainda é o responsavel?', options=['Sim', 'Não'], key=f'responsavel_{id_f}')
                    
                            with c_res_n:

                                if res_select == "Não":
                                    hoje = date.today()

                                    mapeamento = {mb['nome']: mb['cpf'] for mb in st.session_state.membro if mb['nome'].strip() != "" and calcular_idade(mb['data_nasc']) >= 18}
                                    nomes = list(mapeamento.keys())

                                    if nomes:
                                                        
                                        novo_res = st.selectbox("Selecione o novo responsavel",options=nomes, key=f'responsavel_novo_{id_f}')
                                        familia['novo_cpf_responsavel'] = mapeamento[novo_res]
                        if nomes == []:
                                        st.warning("⚠️ Nenhum membro da familia tem maior idade para ser responsavel da família")

                    c_cm, c_tm,c_tm_n = st.columns(3)

                    with c_cm:
                        custo_moradia = st.number_input('Custo moradia',min_value=0.0, value=escolha['custo_moradia'], step=1.0, key=f'custo_moradia_{id_f}')
                        familia['custo_moradia'] = custo_moradia

                    with c_tm:
                        tipo_moradia = st.selectbox("Trocou de tipo de moradia?", options=['Sim', 'Não'], key=f'tipo_moradia_{id_f}')

                        if tipo_moradia == 'Sim':
                            with c_tm_n:
                                todas_moradias = ["Casa Propria", "Cedida", "Aluguel", "Ocupação"]
                                moradia_option = [mor for mor in todas_moradias if mor != escolha['tipo_moradia']]
                                novo_tipo_moradia = st.selectbox("Escolha o novo tipo de moradia", options=moradia_option, key=f'tipo_moradia_novo_{id_f}')
                                familia['tipo_moradia'] = novo_tipo_moradia

                    obs = st.text_area('Observação',placeholder="Observação sobre a familia. Ex: familia aparenta viver em condições insalubres...", key='observacao')
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
                                    st.balloons()


        else:
            st.warning("Nenhuma familia encontrada com esses dados.")