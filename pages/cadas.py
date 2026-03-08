import streamlit as st
import os
from datetime import date, timedelta
from modulos.validacao import  validar_cpf, validar_data, validar_nome, validar_tel
from modulos.database import criar_table, salvar_Familia, nome_bairros, novo_bairro

st.set_page_config(page_title="Monitoramento SLZ", layout="wide")

st.title("Cadastro de Familia - São Luís")
st.write("")

criar_table()

def limpar_dados(membros):
    for m in membros:
        cpfl = m['cpf']

def remover_membro(indice):
    st.session_state.membro.pop(indice)

def reset_form():
    st.session_state.membro = [{
        "nome": "", "erro_nome":"", "cpf": "", "erro_cpf": "", 
        "sexo": "Masculino", "gestante": 0, "pcd": 0, "bairro": '', 
        'tipo_moradia': "Casa Propria ", 'custo_moradia': 0.0, 'renda': 0.0, 
        "erro_renda": "", 'data_nasc': None, 'erro_data': "", 
        "telefone": "", "erro_tel": ""
    }]
    
    st.session_state.form_id += 1
    
    for key in list(st.session_state.keys()):
        if any(x in key for x in ['nome_', 'cpf_', 'bairro_', 'renda_']):
            del st.session_state[key]

def adicionar_membros():
    if len(st.session_state.membro) > 0:
        ultimo = st.session_state.membro[-1]
        if not ultimo["nome"].strip() or not ultimo["cpf"].strip():
            st.toast("Preencha o membro atual antes de adicionar um outro!", icon="🚫")
            return

    st.session_state.membro.append({
        "nome": "", "erro_nome":"", "cpf": "", "erro_cpf": "", 
        "sexo": "Masculino", "gestante": 0, "pcd": 0, "bairro": '', 
        'tipo_moradia': "", 'custo_moradia': 0.0, 'renda': 0.0, 
        "erro_renda": "", 'data_nasc': None, 'erro_data': "",
        "telefone": "", "erro_tel": ""
    })

if 'membro' not in st.session_state:
    st.session_state.membro = []
    st.session_state.membro.append({
        "nome": "", "erro_nome":"", "cpf": "", "erro_cpf": "", 
        "sexo": "Masculino", "gestante": 0, "pcd": 0, "bairro": '', 
        'tipo_moradia': "", 'custo_moradia': 0.0, 'renda': 0.0, 
        "erro_renda": "", 'data_nasc': None, 'erro_data': "", 
        "telefone": "", "erro_tel": ""
    })

if 'banco_familias' not in st.session_state:
    st.session_state.banco_familias = {}

if 'form_id' not in st.session_state:
    st.session_state.form_id = 0

bairros = nome_bairros()
if 'Outro' not in bairros:
    bairros.append('Outro')

col_esq, espaco, col_dir = st.columns([4.5, 1, 4.5])

for i, membro in enumerate(st.session_state.membro):
    coluna_atual = col_esq if i % 2 == 0 else col_dir

    with coluna_atual:
        with st.container(border=True):
            c_header, c_trash = st.columns([0.8, 0.2])

            with c_header:
                label = "Responsavel" if i == 0 else f"Membro {i+1}"
                st.write(label)

            with c_trash:
                if i > 0:
                    st.button("❌", key=f"btn_excluir_{i}", on_click=remover_membro, args=(i,))

            membro['nome'] = st.text_input(f"Nome", placeholder="Nome Completo", on_change=validar_nome, args=(i,), key=f'nome_{i}_{st.session_state.form_id}')
            
            if membro.get('erro_nome'):
                st.error(membro['erro_nome'])
            
            if i == 0:
                c0, c1 = st.columns(2)
                with c0:
                    bairro_s = st.selectbox(f"Bairro", options=bairros, key=f'bairro_{i}_{st.session_state.form_id}')

                with c1:
                    if bairro_s == "Outro":
                        st.text_input(f"Bairro", key=f'input_{i}_{st.session_state.form_id}', placeholder="Nome do bairro", on_change=novo_bairro, args=(i,))

                erro_bairro = st.empty()
                nome_bairro_input = st.session_state.get(f'input_{i}_{st.session_state.form_id}')

                if bairro_s == "Outro":
                    if nome_bairro_input and membro['bairro'] == "":
                        erro_bairro.error(f"⚠️ O local '{nome_bairro_input}' não foi reconhecido.")
                    elif not nome_bairro_input:
                        erro_bairro.error(f"⚠️ Coloque o nome de algum bairro no campo novo.")
                    else:
                        membro['bairro'] = nome_bairro_input
                else:
                    membro['bairro'] = bairro_s

                c2, c3 = st.columns(2)
                with c2:
                    opcoes_moradia = ["Casa Propria", "Cedida", "Aluguel", "Ocupação"]
                    membro['tipo_moradia'] = st.selectbox("Tipo de moradia", options=opcoes_moradia, key=f'tipo_moradia_{i}_{st.session_state.form_id}')
                with c3:
                    membro['custo_moradia'] = st.number_input("Custo de Moradia", step=50.0, min_value=0.0, key=f'custo_moradia_{i}_{st.session_state.form_id}')

            membro['cpf'] = st.text_input(f"CPF", placeholder="00000000000", key=f'cpf_{i}_{st.session_state.form_id}', on_change=validar_cpf, args=(i,))
            if membro.get('erro_cpf'):
                st.error(membro['erro_cpf'])
            
            c4, c5 = st.columns(2)
            with c4:
                membro['renda'] = st.number_input(f"Renda Individual", min_value=0.0, key=f'renda_{i}_{st.session_state.form_id}')
            with c5:
                date_min = date.today() - timedelta(days=43800)
                membro['data_nasc'] = st.date_input(f"Data de Nascimento", min_value=date_min, max_value=date.today(), on_change=validar_data, args=(i,), key=f'data_nasc_{i}_{st.session_state.form_id}')
                if membro.get('erro_data'):
                    st.error(membro['erro_data'])
            
            col_sex, col_ges, col_pcd = st.columns(3)
            with col_sex:
                sexo_select = st.selectbox("Sexo Biológico / Gênero", options=["Masculino", "Feminino", "Não-binário", "Prefiro não informar"], key=f'sexo_{i}_{st.session_state.form_id}')
                membro['sexo'] = sexo_select

            if sexo_select != "Masculino":
                with col_ges:
                    gest_select = st.selectbox("Gestante", options=["Não", "Sim"], key=f'gestante_{i}_{st.session_state.form_id}')
                    membro['gestante'] = 1 if gest_select == "Sim" else 0
            else:
                membro['gestante'] = 0

            with col_pcd:
                pcd_select = st.checkbox("PCD", value=bool(membro['pcd']), key=f'pcd_{i}_{st.session_state.form_id}')
                membro['pcd'] = 1 if pcd_select else 0
                        
            membro['telefone'] = st.text_input(f"Telefone", placeholder="98999999999", on_change=validar_tel, args=(i,), key=f'telefone_{i}_{st.session_state.form_id}')
            if membro.get('erro_tel'):
                st.error(membro['erro_tel']) 

st.write("")

erro_form = False
for i, m in enumerate(st.session_state.membro):

    lista_erros = [
        m.get('erro_cpf'), 
        m.get('erro_nome'), 
        m.get('erro_tel'),
        m.get('erro_data'),
        not m.get('nome').strip(), 
        not m.get('cpf').strip() 
    ]

    if i == 0:
        k_select = f'bairro_{i}_{st.session_state.form_id}'
        k_input = f'input_{i}_{st.session_state.form_id}'
        bairro_void = False

        if st.session_state.get(k_select) == "Outro":
            if not st.session_state.get(k_input):
                bairro_void = True

        lista_erros.append(bairro_void)
        lista_erros.append(not m.get('bairro'))

    if any(lista_erros):
        erro_form = True
        break

c_btn1, c_btn2, c_vazia = st.columns([1.2, 1.5, 4])
with c_btn1:
    msg = "Há campos com erros. Verifique as mensagens em vermelho." if erro_form else "Clique para salvar a família"
    finalizar = st.button("Finalizar cadastro da familia", disabled=erro_form, help=msg if erro_form else None)
    
with c_btn2:
    st.button(' ➕ Membro', on_click=adicionar_membros)
    
if finalizar:
    if len(st.session_state.membro) > 0:
        bairro_f = st.session_state.membro[0]['bairro'].strip()
        moradia_f = st.session_state.membro[0]["tipo_moradia"]
        custo_f = st.session_state.membro[0]["custo_moradia"]
        renda_f = sum([m['renda'] for m in st.session_state.membro])
        quantidade_f = len(st.session_state.membro)
        cpf_responsavel = st.session_state.membro[0]['cpf']
        dados_familia = [m.copy() for m in st.session_state.membro]
        st.session_state.banco_familias[cpf_responsavel] = dados_familia

        try:
            salvar_Familia(dados_familia, bairro_f, moradia_f, custo_f, renda_f, quantidade_f)
            st.button("Cadastrar nova família", on_click=reset_form)
        except Exception as e:
            st.error(f"Erro ao salvar no banco: {e}")
    else:
        st.warning("Adicione pelo menos uma pessoa")