import streamlit as st
import re
import sqlite3
import uuid

st.set_page_config(page_title="Monitoramento SLZ", layout="wide")

st.title ("Cadastro de Familia - São Luís")
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
    for i in range(len(st.session_state.membro)):
        keys_para_deletar = [f'nome_{i}', f'cpf_{i}', f'bairro_{i}', f'tipo_moradia_{i}', f'custo_moradia_{i}', f'renda_{i}', f'data_nasc_{i}', f'telefone_{i}']
        for k in keys_para_deletar:
            if k in st.session_state:
                del st.session_state[k]
    
    st.session_state.membro = [{"nome": "", "cpf": "", "bairro": '', 'tipo_moradia': " ", 'custo_moradia': 0, 'renda': 0.0, 'data_nasc': 0, "telefone": ""}]

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

            st.session_state.membro[i]['nome'] = st.text_input(f"Nome", placeholder = "Nome Completo", key = f'nome_{i}')

            if i == 0:

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.session_state.membro[i]['bairro'] = st.text_input(f"Bairro", placeholder= "Bairro da familia", key= f'bairro_{i}')

                with c2:
                    opcoes = ["Casa Propria", "Cedida", "Aluguel", "Ocupação"]
                    moradia = st.selectbox("Tipo de moradia", options=opcoes, key= f'tipo_moradia_{i}')
                    st.session_state.membro[i]['tipo_moradia'] = moradia

                with c3:
                    if moradia in ["Aluguel", "Cedida"]:

                        label_custo = "Valor do aluguel" if moradia == "Aluguel" else "Custo de moradia (se houver)"
                        st.session_state.membro[i]['custo_moradia'] = st.number_input(label_custo, step=50.0, min_value=0.0, key=f'custo_moradia_{i}')
                    
                    else:

                        st.session_state.membro[i]['custo_moradia'] = 0.0

            st.session_state.membro[i]['cpf'] = st.text_input(f"CPF", placeholder= "00000000000", key = f'cpf_{i}')

            
            c4, c5 = st.columns(2)
            with c4:
             st.session_state.membro[i]['renda'] = st.number_input(f"Renda Individual", min_value= 0.0, key = f'renda_{i}')
            with c5:
             st.session_state.membro[i]['data_nasc'] = st.date_input(f"Data de Nascimento",  key = f'data_nasc_{i}')
        
            st.session_state.membro[i]['telefone'] = st.text_input(f"Telefone", placeholder="98999999999", key = f'telefone_{i}')

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
            
            except Exception as e:
                st.error(f"Erro ao salvar no banco {e}")

            st.button("Cadastrar nova família", on_click=reset_form)

                
    else:
        st.warning("Adicione pelo menos uma pessoa")