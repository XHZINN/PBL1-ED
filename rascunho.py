import streamlit as st
import re
import sqlite3
import uuid
import os

st.set_page_config(page_title="Monitoramento SLZ", layout="wide")

st.title ("Cadastro de Familia - São Luís")

st.markdown('''
    <style>
    [data-testid="stVerticalBlockBorder"] {
            min-height: 580px !important; 
            }
''', unsafe_allow_html=True)

st.write("")

def conexao_bd():
    return sqlite3.connect('Banco_dados.db')

def criar_table():
        conn = conexao_bd()
        trabaiador = conn.cursor()

        trabaiador.execute('''

        CREATE TABLE IF NOT EXISTS Familias(
                           
            uuid_familia TEXT PRIMARY KEY,
            bairro TEXT,
            tipo_moradia TEXT,
            custo_moradia REAL,
            renda_familiar REAL,
            pessoas_familia REAL,
            cpf_responsavel TEXT UNIQUE
               )
        ''')
        trabaiador.execute('''
        CREATE TABLE IF NOT EXISTS Pessoas(

            uuid_pessoa TEXT PRIMARY KEY,
            uuid_familia TEXT,
            nome TEXT,
            cpf TEXT UNIQUE,
            renda REAL,
            data_nasc TEXT, 
            telefone TEXT
                )
        ''')

        conn.commit()
        conn.close()

criar_table()

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

def validar_dados(cpf, nome, telefone):
    regra_cpf = r"^\d{11}$"

    regra_nome = r"^[A-Za-zÀ-ÿ ]{3,}$"

    regra_tel = r"^\d{10,11}$"
   
    cpfn = re.sub(r'\D', '', cpf)
    nomen = nome.strip()
    teln = re.sub(r'\D', '', telefone)
   
    if not cpfn or not nomen or not teln:
        return False, "Há campos vazios, Por favor faça o preenchimento de todos!"

    if not re.match(regra_cpf, cpfn):
        return False, "CPF invalido! Digite apenas 11 numeros"
    
    if not re.match(regra_nome, nomen):
        return False, "Nome invalido! Por favor insira apenas letras e acentos"
    
    if not re.match(regra_tel, teln):
        return False, "Número telefone invalido! Digite um número telefone valido"
    
    return True, "Dados Validos"

def remover_membro(indice):
    st.session_state.membro.pop(indice)

def reset_form():

    st.session_state.membro = [{"nome": "", "cpf": "", "bairro": "", "tipo_moradia": "Casa Propria", "custo_moradia": 0.0, "renda": 0.0, "data_nasc": None, "telefone": ""}]
    
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

    st.session_state.membro.append({"nome": " ", "cpf": " ", "bairro": '', 'tipo_moradia': " ", 'custo_moradia': 0, 'renda': 0.0, 'data_nasc': 0, "telefone": " "})

if 'membro' not in st.session_state:
    st.session_state.membro = []

    st.session_state.membro.append({"nome": " ", "cpf": " ", 'bairro': "", 'tipo_moradia': " ", 'custo_moradia': 0, 'renda': 0.0, 'data_nasc': 0, "telefone": " "})

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
              label = "Responsavel" if i == 0 else f"{i+1}° Membro"
              st.write(label)

            with c_trash:
                if i > 0:
                    st.button("❌", key=f"btn_excluir_{i}", on_click=remover_membro, args=(i,))

            st.session_state.membro[i]['nome'] = st.text_input(f"Nome", placeholder = "Nome Completo", key = f'nome_{i}_{st.session_state.form_id}')

            if i == 0:

                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    
                    select_bairro = st.selectbox(f"Bairro", options=bairros, key= f'bairro_{i}_{st.session_state.form_id}')

                with c2:
                    if select_bairro == 'Outros':
                        bairro_final = st.text_input (placeholder='Digite o nome do Bairro', label='Bairro', key=f'bm_{i}_{st.session_state.form_id}',)
                    else:
                        bairro_final = select_bairro

                    st.session_state.membro[i]['bairro'] = bairro_final

                with c3:
                    opcoes = ["Casa Propria", "Cedida", "Aluguel", "Ocupação"]
                    moradia = st.selectbox("Tipo de moradia", options=opcoes, key= f'tipo_moradia_{i}_{st.session_state.form_id}')
                    st.session_state.membro[i]['tipo_moradia'] = moradia

                with c4:
                    if moradia in ["Aluguel", "Cedida"]:

                        label_custo = "Valor do aluguel" if moradia == "Aluguel" else "Custo de moradia (se houver)"
                        st.session_state.membro[i]['custo_moradia'] = st.number_input(label_custo, step=50.0, min_value=0.0, key=f'custo_moradia_{i}_{st.session_state.form_id}')
                    
                    else:

                        st.session_state.membro[i]['custo_moradia'] = 0.0
            
            st.session_state.membro[i]['cpf'] = st.text_input(f"CPF", placeholder= "00000000000", key = f'cpf_{i}_{st.session_state.form_id}')

            
            c5, c6 = st.columns(2)

            with c5:
             st.session_state.membro[i]['renda'] = st.number_input(f"Renda Individual", min_value= 0.0, key = f'renda_{i}_{st.session_state.form_id}')
            
            with c6:
             st.session_state.membro[i]['data_nasc'] = st.date_input(f"Data de Nascimento",  key = f'data_nasc_{i}_{st.session_state.form_id}')
        
            st.session_state.membro[i]['telefone'] = st.text_input(f"Telefone", placeholder="98999999999", key = f'telefone_{i}_{st.session_state.form_id}')

st.write("")

c_btn1, c_btn2, c_vazia = st.columns([1.2, 1.5, 4])

with c_btn1:
    st.button(' ➕ Membro', on_click = adicionar_membros)

with c_btn2:
    finalizar = st.button("Finalizar cadastro da familia")


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