import streamlit as st
import re
import sqlite3

st.set_page_config(page_title="Monitoramento SLZ", layout="wide")

st.title ("Cadastro de Familia - São Luís")
st.write("")

def conexao():
    return sqlite3.connect('Banco_dados.db')

def criar_table():
        conn = conexao()
        pen = conn.cursor('''

        CREATE TABLE IF NOT EXISTS Familias


        ''')

        pen.execute()

if 'membro' not in st.session_state:
    st.session_state.membro = []

    st.session_state.membro.append({"nome": " ", "cpf": " ", 'bairro': "", 'renda': 0.0, 'idade': 0, "telefone": " "})

if 'banco_familias' not in st.session_state:
    st.session_state.banco_familias = {}

def validar_dados(cpf, nome, telefone, bairro):
    regra_cpf = r"^\d{11}$"

    regra_nome = r"^[A-Za-zÀ-ÿ ]{3,}$"

    regra_tel = r"^\d{10,11}$"
   
    cpfn = re.sub(r'\D', '', cpf)
    nomen = nome.strip()
    teln = re.sub(r'\D', '', telefone)
   
    if not cpfn or not nomen or not teln or not bairro:
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
        keys_para_deletar = [f'nome_{i}', f'cpf_{i}', f'bairro', f'renda_{i}', f'idade_{i}', f'telefone_{i}']
        for k in keys_para_deletar:
            if k in st.session_state:
                del st.session_state[k]
    
    st.session_state.membro = [{"nome": "", "cpf": "", "bairro": '', 'renda': 0.0, 'idade': 0, "telefone": ""}]

def adicionar_membros():
    if len(st.session_state.membro) > 0:

        ultimo = st.session_state.membro[-1]

        if not ultimo["nome"].strip() or not ultimo["cpf"].strip():
            st.toast("Preencha o membro atual antes de adicionar um outro!", icon = "🚫")
            return

    st.session_state.membro.append({"nome": " ", "cpf": " ", "bairro": '', "tipo_moradia": '', 'renda': 0.0, 'idade': 0, "telefone": " "})

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
                st.session_state.membro[i]['bairro'] = st.text_input(f"Bairro", placeholder= "Bairro da familia", key= f'bairro_{i}')

                st.session_state.membro[i]['tipo_moradia'] = st.text_input("Tipo de moradia", placeholder= "Tipo de moradia", key= f'tipo_moradia_{i}')

            st.session_state.membro[i]['cpf'] = st.text_input(f"CPF", placeholder= "00000000000", key = f'cpf_{i}')
            
            c1, c2 = st.columns(2)
            with c1:
             st.session_state.membro[i]['renda'] = st.number_input(f"Renda Individual", min_value= 0.0, key = f'renda_{i}')
            with c2:
             st.session_state.membro[i]['idade'] = st.number_input(f"Idade", min_value= 0, step = 1, key = f'idade_{i}')
        
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

        for m in st.session_state.membro:
            valido, msg = validar_dados(m['cpf'], m['nome'], m['telefone'], m['bairro'])
            if not valido:
                st.error(f"Erro no {m['nome'] if m['cpf'] else 'Membro'}: {msg}")
                valido = False
                break

        if valido:

            ttl_renda = sum(m['renda'] for m in st.session_state.membro)
            qtd_pessoa = len(st.session_state.membro)
            RP = ttl_renda / qtd_pessoa

            st.metric("Renda per capita da familia", f"R$ {RP:.2f}")

            cpf_responsavel = st.session_state.membro[0]['cpf']
            st.session_state.banco_familias[cpf_responsavel] = [m.copy() for m in st.session_state.membro]
            
            st.success(f"Familia do responsavel correspondente ao CPF: {cpf_responsavel} cadastrada com sucesso!")

            st.button("Cadastrar nova família", on_click=reset_form)

                
    else:
        st.warning("Adicione pelo menos uma pessoa")
        