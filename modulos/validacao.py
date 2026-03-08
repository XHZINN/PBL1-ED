import re
import streamlit as st
from datetime import date
import unicodedata

def validar_cpf(indice):

    k_cpf = f'cpf_{indice}_{st.session_state.form_id}'
    cpf = st.session_state.get(k_cpf)

    if not cpf:
        st.session_state.membro[indice]['erro_cpf'] = ""
        return

    cpf = re.sub(r'\D', '', str(cpf))

    if len(cpf) != 11:
        st.session_state.membro[indice]['erro_cpf'] = "CPF deve conter 11 digitos "
        st.session_state.membro[indice]['cpf'] = ""
        return

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
        st.session_state.membro[indice]['erro_cpf'] = "Padrão de CPF inválido"
    

    else:
        st.session_state.membro[indice]['erro_cpf'] = ""

def validar_nome(indice):

    k_nome = st.session_state[f'nome_{indice}_{st.session_state.form_id}']

    if len(k_nome) > 0 and len(k_nome) < 2:
        st.session_state.membro[indice]['erro_nome'] = "Nome muito curto (mínimo 2 letras)"
        return

    padrao = r"^[A-Za-zÀ-ÿ]+(?:[ \-\'’´][A-Za-zÀ-ÿ]*)*$"

    if not k_nome:
        st.session_state.membro[indice]['erro_nome'] = ""
        return

    if not re.match(padrao, k_nome):
        st.session_state.membro[indice]['erro_nome'] = "Nome fora do padrão"

    else:
        st.session_state.membro[indice]['erro_nome'] = ""

def validar_data(indice):

    if indice == 0:
        k_data = st.session_state[f'data_nasc_{indice}_{st.session_state.form_id}']
        
        hoje = date.today()
        dias = (hoje - k_data).days

        if dias < 6575:
            st.session_state.membro[indice]['erro_data'] = "O responsável deve ter pelo menos 18 anos."

        else: 
            st.session_state.membro[indice]['erro_data'] = ""
    else:
        st.session_state.membro[indice]['erro_data'] = ""

def validar_tel(indice):

    k_tel1 = st.session_state[f'telefone_{indice}_{st.session_state.form_id}']
    k_tel = k_tel1.strip()

    padrao = r'^\(?([1-9]{2})\)?\s?([9]?\d{4})-?(\d{4})$'

    if not k_tel:
        st.session_state.membro[indice]['erro_tel'] = ""
        return
    if k_tel[:1] == "(":
     ddd_atual = k_tel[1:3]
    else:
     ddd_atual = k_tel[:2]

    if not re.match(padrao, k_tel):
        st.session_state.membro[indice]['erro_tel'] = "Telefone fora do padrão"
        return

    elif not ddd_atual in ["99", "98" ]:
        st.session_state.membro[indice]['erro_tel'] = "DDD não pertence ao Maranhão meu jovem"

    else:
        st.session_state.membro[indice]['erro_tel'] = ""

def validar_dados(cpf, nome, telefone):
    regra_cpf = r'^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$'

    regra_nome = r"^[A-Za-zÀ-ÿ]+(?:[ \-\'’´][A-Za-zÀ-ÿ]*)*$"

    regra_tel = r'^\(?([1-9]{2})\)?\s?([9]?\d{4})-?(\d{4})$'
   
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

def limpar(t):
     
     return "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn').casefold()

def limpar_somente_numeros(valor):
    if valor and isinstance(valor, str):
        return re.sub(r'\D', '', valor) # \D é um atalho para "tudo que não é dígito"
    return str(valor) if valor else ""

