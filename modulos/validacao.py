import re
import streamlit as st
from datetime import date
import unicodedata

def validar_cpf(indice, is_visita=False):
    # Abstração de chaves e listas
    if is_visita:
        k_cpf_key = f'cpf_novo_{indice}'
        lista_key = 'membro'
    else:
        f_id = st.session_state.get('form_id', '')
        k_cpf_key = f'cpf_{indice}_{f_id}'
        lista_key = 'membro'

    cpf_bruto = st.session_state.get(k_cpf_key)
    membro_atual = st.session_state[lista_key][indice]

    if not cpf_bruto:
        membro_atual['erro_cpf'] = ""
        return

    cpf = re.sub(r'\D', '', str(cpf_bruto))

    if len(cpf) != 11:
        membro_atual['erro_cpf'] = "CPF deve conter 11 dígitos"
        return

    # Sua lógica matemática de validação
    soma = 0
    for n in range(9):
        soma += int(cpf[n]) * (10 - n)
    resto = (soma * 10) % 11
    digito_1 = resto if resto < 10 else 0
    
    soma = 0
    for n in range(10):
        soma += int(cpf[n]) * (11 - n)
    resto = (soma * 10) % 11
    digito_2 = resto if resto < 10 else 0

    if cpf == cpf[0] * 11 or int(cpf[9]) != digito_1 or int(cpf[10]) != digito_2:
        membro_atual['erro_cpf'] = "Padrão de CPF inválido"
    else:
        membro_atual['erro_cpf'] = ""

def validar_nome(indice, is_visita=False):
    if is_visita:
        key_widget = f"nome_novo_{indice}"
        lista_key = "membro"
    else:
        
        f_id = st.session_state.get('form_id', '')
        key_widget = f"nome_{indice}_{f_id}"
        lista_key = "membro"

    k_nome = st.session_state.get(key_widget, "")

    membro_atual = st.session_state[lista_key][indice]

    if not k_nome:
        membro_atual['erro_nome'] = ""
        return

    if 0 < len(k_nome) < 2:
        membro_atual['erro_nome'] = "Nome muito curto (mínimo 2 letras)"
        return

    padrao = r"^[A-Za-zÀ-ÿ]+(?:[ \-\'’´][A-Za-zÀ-ÿ]*)*$"

    if not re.match(padrao, k_nome):
        membro_atual['erro_nome'] = "Nome fora do padrão"
    else:
        membro_atual['erro_nome'] = ""

def validar_data(indice, is_visita=False):
    if is_visita:
        k_data_key = f'data_nasc_{indice}'
        lista_key = 'membro'
    else:
        f_id = st.session_state.get('form_id', '')
        k_data_key = f'data_nasc_{indice}_{f_id}'
        lista_key = 'membro'

    data_nasc = st.session_state.get(k_data_key)
    membro_atual = st.session_state[lista_key][indice]

    # Validação apenas para o RESPONSÁVEL (índice 0)
    if indice == 0 and data_nasc:
        hoje = date.today()
        dias = (hoje - data_nasc).days

        if dias < 6575:
            membro_atual['erro_data'] = "O responsável deve ter pelo menos 18 anos."
        else: 
            membro_atual['erro_data'] = ""
    else:
        membro_atual['erro_data'] = ""

def validar_tel(indice, is_visita=False):
    if is_visita:
        k_tel_key = f'telefone_novo_{indice}' 
        lista_key = 'membro'
    else:
        f_id = st.session_state.get('form_id', '')
        k_tel_key = f'telefone_{indice}_{f_id}'
        lista_key = 'membro'

    k_tel = str(st.session_state.get(k_tel_key, "")).strip()
    membro_atual = st.session_state[lista_key][indice]

    if not k_tel:
        membro_atual['erro_tel'] = ""
        return

    padrao = r'^\(?([1-9]{2})\)?\s?([9]?\d{4})-?(\d{4})$'
    
    # Lógica do DDD Maranhense
    ddd_atual = k_tel[1:3] if k_tel.startswith("(") else k_tel[:2]

    if not re.match(padrao, k_tel):
        membro_atual['erro_tel'] = "Telefone fora do padrão"
    elif ddd_atual not in ["99", "98"]:
        membro_atual['erro_tel'] = "DDD não pertence ao Maranhão meu jovem"
    else:
        membro_atual['erro_tel'] = ""

def limpar(t):
     
     return "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn').casefold()

def limpar_somente_numeros(valor):
    if valor and isinstance(valor, str):
        return re.sub(r'\D', '', valor) # \D é um atalho para "tudo que não é dígito"
    return str(valor) if valor else ""

