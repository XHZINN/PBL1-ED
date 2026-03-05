import streamlit as st
import sqlite3
import uuid
import os
from datetime import date, timedelta
from modulos.validacao import validar_dados, validar_cpf, validar_data, validar_nome, validar_tel
from modulos.database import criar_table, conexao_bd, salvar_bd

st.set_page_config(page_title="Monitoramento SLZ", layout="wide")

st.title ("Cadastro de Familia - São Luís")
st.write("")

criar_table()

def limpar_dados(membros):

    for m in membros:
        cpfl = m['cpf']

def salvar_bd(membros, bairro_f, moradia_f, custo_f, renda_f, quantidade_f):

    uuid_familia = str(uuid.uuid4())
    conn = conexao_bd()
    pen = conn.cursor()

    try:

        pen.execute('''

            INSERT INTO Familias(uuid_familia, bairro, tipo_moradia, custo_moradia, renda_familiar,pessoas_familia, cpf_responsavel)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (uuid_familia, bairro_f, moradia_f, custo_f, renda_f, quantidade_f, st.session_state.membro[0]['cpf']))
        for m in membros:
            uuid_pessoa = str(uuid.uuid4())
            pen.execute('''

            INSERT INTO Pessoas(uuid_pessoa, uuid_familia, nome, cpf, renda, data_nasc, telefone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (uuid_pessoa, uuid_familia, m['nome'], m['cpf'], m['renda'], m['data_nasc'], m['telefone']))
        conn.commit()
        st.success("Família e Membros salvos com sucesso")

    except sqlite3.IntegrityError:
            st.error("Erro: Um dos CPFs já está cadastrado no sistema!")
    finally:
        conn.close()
    
def bairros_slz():
    path_B = 'bairros_slz.txt'

    if os.path.exists(path_B):
        with open (path_B, 'r', encoding= 'utf-8') as b:

            bairros = [linha.strip() for linha in b.readlines() if linha.strip()]
            return sorted(bairros)
    else:
        return ['Centro', 'Cohab', 'Turu', 'Outros']

def remover_membro(indice):
    st.session_state.membro.pop(indice)

def reset_form():

    st.session_state.membro = [{"nome": " ", "erro_nome":"", "cpf": " ", "erro_cpf": "", "bairro": '', 'tipo_moradia': "Casa Propria ", 'custo_moradia': 0.0, 'renda': 0.0, "erro_renda": "", 'data_nasc': None, 'erro_data': "", "telefone": " ", "erro_tel": ""}]
    
    st.session_state.form_id += 1
    
    for key in list(st.session_state.keys()):
        if any(x in key for x in ['nome_', 'cpf_', 'bairro_', 'renda_']):
            del st.session_state[key]

def adicionar_membros():
    if len(st.session_state.membro) > 0:

        ultimo = st.session_state.membro[-1]

        if not ultimo["nome"].strip() or not ultimo["cpf"].strip():
            st.toast("Preencha o membro atual antes de adicionar um outro!", icon = "🚫")
            return

    st.session_state.membro.append({"nome": " ", "erro_nome":"", "cpf": " ", "erro_cpf": "", "bairro": '', 'tipo_moradia': " ", 'custo_moradia': 0.0, 'renda': 0.0, "erro_renda": "", 'data_nasc': None, 'erro_data': "","telefone": " ", "erro_tel": ""})

if 'membro' not in st.session_state:
    st.session_state.membro = []

    st.session_state.membro.append({"nome": " ", "erro_nome":"", "cpf": " ", "erro_cpf": "", "bairro": '', 'tipo_moradia': " ", 'custo_moradia': 0.0, 'renda': 0.0, "erro_renda": "", 'data_nasc': None, 'erro_data': "", "telefone": " ", "erro_tel": ""})

if 'banco_familias' not in st.session_state:

    st.session_state.banco_familias = {}

if 'form_id' not in st.session_state:
    st.session_state.form_id = 0

bairros = bairros_slz()
if 'Outros' not in bairros:
    bairros.append('Outros')

col_esq, espaco, col_dir = st.columns([4.5, 1, 4.5])

for i, membro in enumerate(st.session_state.membro):

    coluna_atual = col_esq if i % 2 == 0 else col_dir

    with coluna_atual:
        with st.container(border= True):

            c_header, c_trash = st.columns([0.8, 0.2])

            with c_header:
              label = "Responsavel" if i == 0 else f"Membro {i+1}"
              st.write(label)

            with c_trash:
                if i > 0:
                    st.button("❌", key=f"btn_excluir_{i}", on_click=remover_membro, args=(i,))

            st.session_state.membro[i]['nome'] = st.text_input(f"Nome", placeholder = "Nome Completo", on_change=validar_nome, args=(i,), key = f'nome_{i}_{st.session_state.form_id}')
            if st.session_state.membro[i].get('erro_nome'):
                st.error(st.session_state.membro[i]['erro_nome'])
            if i == 0:

                c1, c2, c3 = st.columns(3)

                with c1:
                    
                    st.session_state.membro[i]['bairro'] = st.selectbox(f"Bairro", options=bairros, key= f'bairro_{i}_{st.session_state.form_id}')

                with c2:
                    opcoes = ["Casa Propria", "Cedida", "Aluguel", "Ocupação"]
                    moradia = st.selectbox("Tipo de moradia", options=opcoes, key= f'tipo_moradia_{i}_{st.session_state.form_id}')
                    st.session_state.membro[i]['tipo_moradia'] = moradia

                with c3:
                    if moradia in ["Aluguel", "Cedida"]:

                        label_custo = "Valor do aluguel" if moradia == "Aluguel" else "Custo de moradia (se houver)"
                        st.session_state.membro[i]['custo_moradia'] = st.number_input(label_custo, step=50.0, min_value=0.0, key=f'custo_moradia_{i}_{st.session_state.form_id}')
                    
                    else:

                        st.session_state.membro[i]['custo_moradia'] = 0.0

            st.session_state.membro[i]['cpf'] = st.text_input(f"CPF", placeholder= "00000000000", key = f'cpf_{i}_{st.session_state.form_id}', on_change=validar_cpf, args=(i,))
            if st.session_state.membro[i].get('erro_cpf'):
                st.error(st.session_state.membro[i]['erro_cpf'])
            
            c4, c5 = st.columns(2)
            with c4:
             st.session_state.membro[i]['renda'] = st.number_input(f"Renda Individual", min_value= 0.0, key = f'renda_{i}_{st.session_state.form_id}')
            with c5:
             
             date_min = date.today() - timedelta(days=43800)
             
             st.session_state.membro[i]['data_nasc'] = st.date_input(f"Data de Nascimento", min_value=date_min, max_value=date.today(), on_change=validar_data, args=(i,), key = f'data_nasc_{i}_{st.session_state.form_id}')
            if st.session_state.membro[i].get('erro_data'):
             st.error(st.session_state.membro[i]['erro_data'])

            st.session_state.membro[i]['telefone'] = st.text_input(f"Telefone", placeholder="98999999999", on_change=validar_tel, args=(i,)  ,key = f'telefone_{i}_{st.session_state.form_id}')
            if st.session_state.membro[i].get('erro_tel'):
                st.error(st.session_state.membro[i]['erro_tel'])
st.write("")

erro_form = False

for m in st.session_state.membro:
    if any([m.get('erro_cpf'), m.get('erro_nome'), m.get('erro_tel'), m.get('erro_data')]):
        erro_form = True
        break

c_btn1, c_btn2, c_vazia = st.columns([1.2, 1.5, 4])

with c_btn1:

    msg = "Há campos com erros. Verifique as mensagens em vermelho." if erro_form else "Clique para salva a família"
    finalizar = st.button("Finalizar cadastro da familia", disabled=erro_form, help=msg if erro_form else None)
    
with c_btn2:
    st.button(' ➕ Membro', on_click = adicionar_membros)
    
if finalizar:
    if len(st.session_state.membro) > 0:
        valido = True

        bairro_f = st.session_state.membro[0]['bairro'].strip()
        moradia_f = st.session_state.membro[0]["tipo_moradia"]
        custo_f = st.session_state.membro[0]["custo_moradia"]
        renda_f = sum([m['renda'] for m in st.session_state.membro])
        quantidade_f = len(st.session_state.membro)


        if not bairro_f:
            st.error("O campo bairro está vazio, Por favor preencher")

        
        for m in st.session_state.membro:
            valido, msg = validar_dados(m['cpf'], m['nome'], m['telefone'])
            if not valido:
                st.error(f"Erro no {m['nome'] if m['cpf'] else 'Membro'}: {msg}")
                valido = False
                break

        if valido:


            cpf_responsavel = st.session_state.membro[0]['cpf']
            dados_familia = [m.copy() for m in st.session_state.membro]
            st.session_state.banco_familias[cpf_responsavel] = dados_familia

            try:
                salvar_bd(dados_familia, bairro_f, moradia_f, custo_f, renda_f, quantidade_f)
                st.button("Cadastrar nova família", on_click=reset_form)
             
            except Exception as e:
                st.error(f"Erro ao salvar no banco {e}")

                
    else:
        st.warning("Adicione pelo menos uma pessoa")