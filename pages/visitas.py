import streamlit as st
import pandas as pd
from datetime import date, timedelta
from modulos.database import buscar_responsavel_por_cpf_ou_nome, registrar_visita, buscar_membros_familia
from modulos.validacao import validar_cpf, validar_data, validar_nome, validar_tel

def adicionar_novo_membro():
    if 'membros_edicao' in st.session_state:
        novo = {
            "nome": "", "cpf": "", "sexo": "Masculino", 
            "gestante": 0, "pcd": 0, "renda": 0.0, 
            "data_nasc": date.today(), "telefone": "",
            "uuid_familia": st.session_state.familia_visita['uuid_familia'],
            "erro_cpf": None, "erro_data": None, "erro_nome": None
        }
        st.session_state.membros_edicao.append(novo)

st.title("📍 Acompanhamento e Visitas Técnicas")

# 1. BUSCA DE FAMÍLIA (Mantido conforme seu código)
with st.expander("🔍 Localizar Família", expanded=True):
    busca = st.text_input("Busca por CPF do Responsável ou Nome")
    if busca:
        dados = buscar_responsavel_por_cpf_ou_nome(busca)
        if dados:
            df_busca = pd.DataFrame(dados)
            def formatar_exibicao(uuid_familia):
                linha = df_busca[df_busca['uuid_familia'] == uuid_familia].iloc[0]
                return f"{linha['nome']} - CPF: {linha['cpf']}"

            escolha_uuid = st.selectbox(
                "Selecione a família encontrada:",
                options=df_busca['uuid_familia'].tolist(),
                format_func=formatar_exibicao
            )
            if escolha_uuid:
                if 'familia_visita' in st.session_state:
                    if st.session_state.familia_visita['uuid_familia'] != escolha_uuid:
                        # Limpamos os membros antigos para forçar uma nova busca no banco
                        if 'membros_edicao' in st.session_state:
                            del st.session_state.membros_edicao
                # ----------------------------

                familia_selecionada = df_busca[df_busca['uuid_familia'] == escolha_uuid].iloc[0].to_dict()
                st.session_state.familia_visita = familia_selecionada
        else:
            st.warning("Nenhum responsável encontrado.")

# 2. FORMULÁRIO DE VISITA
if 'familia_visita' in st.session_state:
    f = st.session_state.familia_visita
    
    if 'membros_edicao' not in st.session_state:
        st.session_state.membros_edicao = buscar_membros_familia(f['uuid_familia'])

    st.subheader(f"📝 Atualização de Visita: Família de {f['nome']}")

    st.write("### 👥 Membros da Família")
    novos_dados_membros = []
    
    for i, membro in enumerate(st.session_state.membros_edicao):
        with st.container(border=True):
            # Se for membro novo (sem nome no banco), habilitamos validações de Nome, CPF e Data
            if membro.get('nome') == "":
                st.write(f"**Novo Membro {i+1}**")
                
                m_nome = st.text_input("Nome Completo", key=f"nome_novo_{i}", 
                                      on_change=validar_nome, args=(i, True)) # True indica modo edição/visita se sua função suportar
                if membro.get('erro_nome'): st.error(membro['erro_nome'])

                col_cpf, col_dn = st.columns(2)
                with col_cpf:
                    m_cpf = st.text_input("CPF", key=f"cpf_novo_{i}", max_chars=11, 
                                         on_change=validar_cpf, args=(i, True))
                    if membro.get('erro_cpf'): st.error(membro['erro_cpf'])
                
                with col_dn:
                    date_min = date.today() - timedelta(days=43800)
                    m_data_nasc = st.date_input(f"Data de Nascimento", min_value=date_min, max_value=date.today(), 
                                               on_change=validar_data, args=(i, True), key=f'data_nasc_{i}')
                    if membro.get('erro_data'): st.error(membro['erro_data'])
            else:
                # Membro já existente: Nome e CPF fixos para segurança
                st.write(f"**{membro['nome']}**")
                m_nome = membro['nome']
                m_cpf = membro['cpf']
                m_data_nasc = membro.get('data_nasc')

            c1, c2, c3 = st.columns(3)
            with c1:
                m_renda = st.number_input(f"Renda (R$)", value=float(membro['renda']), key=f"renda_{i}")
            with c2:
                m_sexo = membro['sexo'] if membro.get('nome') != "" else st.selectbox("Sexo", ["Masculino", "Feminino"], key=f"sexo_{i}")
                
                if m_sexo != "Masculino":
                    idx_gest = 1 if membro['gestante'] == 1 else 0
                    m_gest = st.selectbox("Gestante?", ["Não", "Sim"], index=idx_gest, key=f"gest_{i}")
                else:
                    m_gest = "Não"
            with c3:
                idx_pcd = 1 if membro['pcd'] == 1 else 0
                m_pcd = st.selectbox("PCD?", ["Não", "Sim"], index=idx_pcd, key=f"pcd_{i}")

            m_at = membro.copy()
            m_at['nome'] = m_nome
            m_at['cpf'] = m_cpf
            m_at['renda'] = m_renda
            m_at['gestante'] = 1 if m_gest == "Sim" else 0
            m_at['pcd'] = 1 if m_pcd == "Sim" else 0
            m_at['data_nasc'] = m_data_nasc
            novos_dados_membros.append(m_at)

    st.button("➕ Adicionar outro membro a esta família", on_click=adicionar_novo_membro)
    st.divider()

    # --- PARTE 2: DADOS GERAIS ---
    st.write("### 🏠 Dados Gerais do Atendimento")
    col_gen1, col_gen2 = st.columns(2)
    with col_gen1:
        beneficio_entregue = st.selectbox("Recebeu auxílio/cesta básica?", options=["Não", "Sim"])
        recebeu_auxilio = 1 if beneficio_entregue == "Sim" else 0
    with col_gen2:
        observacoes_gerais = st.text_area("Observações da Visita", placeholder="Descreva aqui...")

    if st.button("💾 Salvar Visita e Atualizar Tudo", type="primary"):
        # Verificação final de erros antes de salvar
        tem_erros = any(m.get('erro_cpf') or m.get('erro_nome') or m.get('erro_data') for m in novos_dados_membros)
        
        if tem_erros:
            st.error("Por favor, corrija os erros nos dados dos membros antes de salvar.")
        else:
            renda_total = sum(m['renda'] for m in novos_dados_membros)
            sucesso = registrar_visita(f['uuid_familia'], novos_dados_membros, renda_total, recebeu_auxilio, observacoes_gerais)
            
            if sucesso:
                st.success("Tudo atualizado!")
                st.balloons()
                for key in ['membros_edicao', 'familia_visita']:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()