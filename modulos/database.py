import sqlite3
import streamlit as st
import uuid

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
    
def pegar_totais():
    conn = conexao_bd()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM Familias')
    total_familias = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(pessoas_familia) FROM Familias')
    resultado_pessoas = cursor.fetchone()[0]
    total_pessoas = resultado_pessoas if resultado_pessoas else 0
    
    conn.close()
    return total_familias, total_pessoas