import sqlite3
import streamlit as st
import uuid
from geopy import Nominatim
import datetime
import shutil
import os
from modulos.validacao import limpar_somente_numeros, limpar

def backup():
    
    if not os.path.isdir('Backups'):
         os.mkdir("Backups")

    banco_dados = "Banco_dados.db"
    nome_backup = f"backup_{datetime.today()}.db"

    path = os.path.join("Backups", nome_backup)

    shutil.copy2(banco_dados, path)

    return f"Backup {nome_backup} foi feito com sucesso!"


def conexao_bd():
    return sqlite3.connect('Banco_dados.db')

def salvar_Bairro(nome_b, local):

    conn = conexao_bd()
    cursor = conn.cursor()

    

    lat = local.latitude
    lon = local.longitude


    id_bairro = str(uuid.uuid4())

    cursor.execute('''
                    
                    INSERT INTO Bairros(uuid_bairro, nome_bairro, latitude, longitude)
                    VALUES (?, ?, ?, ?)
                    ''', (id_bairro, nome_b.title(), lat, lon))

    conn.commit()

def novo_bairro(indice):
     
     k_bairro = f'input_{indice}_{st.session_state.form_id}'
     nome_b = st.session_state.get(k_bairro)

     if not nome_b:
          return

     conn = conexao_bd()

     bairros = [linha[0] for linha in conn.execute('SELECT nome_bairro FROM Bairros').fetchall()]
     conn.close()

     if limpar(nome_b) in [limpar(b) for b in bairros]:
          st.session_state.membro[indice]['bairro'] = nome_b.title()
          return 
     
     geolocator = Nominatim(user_agent="buscar_bairro")
     busca_b = f"{nome_b}, São Luis, MA, Brasil" 

     try:

        local = geolocator.geocode(busca_b, timeout=10)

        if local and ("São Luís" in local.address or "Sao Luis" in local.address):

            salvar_Bairro(nome_b, local)
            st.session_state.membro[indice]['bairro'] = nome_b.title()
            return     
     except Exception as e:
         print(f"Erro na API: {e}")
    
     st.session_state.membro[indice]['bairro'] = ""

def nome_bairros():
     
     conn = conexao_bd()
     cursor = conn.cursor()

     cursor.execute('SELECT nome_bairro FROM Bairros ORDER BY nome_bairro ASC')

     bairros = [linha[0] for linha in cursor.fetchall()]

     conn.close
     return bairros

def bairros_query():
     
     conn = conexao_bd()
     cursor = conn.cursor()

     cursor.execute('SELECT nome_bairro, latitude, longitude FROM Bairros ORDER BY nome_bairro ASC')
     dados = cursor.fetchall()

     bairros = [{
          
          'bairro': linha[0],
          'lat': linha[1],
          'lon': linha[2],
          'intensidade': 0.5
         }
        for linha in dados
     ]

     conn.close()
     return bairros
  
def criar_table():
        conn = conexao_bd()
        trabaiador = conn.cursor()

        trabaiador.execute('''
        CREATE TABLE IF NOT EXISTS Bairros(
            uuid_bairro TEXT PRIMARY KEY NOT NULL,
            nome_bairro TEXT UNIQUE NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            zona TEXT
                )
        ''')

        trabaiador.execute('''

        CREATE TABLE IF NOT EXISTS Familias(
                           
            uuid_familia TEXT PRIMARY KEY NOT NULL,
            uuid_bairro TEXT NOT NULL,
            tipo_moradia TEXT NOT NULL,
            custo_moradia REAL NOT NULL,
            renda_familiar REAL NOT NULL,
            pessoas_familia REAL,
            cpf_responsavel TEXT UNIQUE NOT NULL,
            FOREIGN KEY (uuid_bairro) REFERENCES Bairros(uuid_bairro)
               )
        ''')
        trabaiador.execute('''
        CREATE TABLE IF NOT EXISTS Pessoas(

            uuid_pessoa TEXT PRIMARY KEY NOT NULL,
            uuid_familia TEXT NOT NULL,
            nome TEXT NOT NULL,
            sexo TEXT NOT NULL,
            gestante INTEGER NOT NULL,
            pcd INTEGER NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            renda REAL,
            data_nasc TEXT NOT NULL, 
            telefone TEXT,
            FOREIGN KEY (uuid_familia) REFERENCES Familias(uuid_familia)
                )
        ''')

        trabaiador.execute(''''
        CREATE TABLE IF NOT EXISTS Backup(
            
            uuid_backup INTEGER PRIMARY KEY NOT NULL,
            nome_backup TEXT NOT NULL,
            caminho TEXT NOT NULL,
            data_criacao DATETIME NOT NULL,
            tipo TEXT              
                )
            ''')

        

        conn.commit()
        conn.close()

def salvar_Familia(membros, bairro_f, moradia_f, custo_f, renda_f, quantidade_f):

    uuid_familia = str(uuid.uuid4())
    conn = conexao_bd()
    pen = conn.cursor()

    for m in membros:
         m['cpf'] = limpar_somente_numeros(m['cpf'])
         m['telefone'] = limpar_somente_numeros(m['telefone'])
    try:

        pen.execute('''

            INSERT INTO Familias(uuid_familia, uuid_bairro, tipo_moradia, custo_moradia, renda_familiar, pessoas_familia, cpf_responsavel)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (uuid_familia, bairro_f, moradia_f, custo_f, renda_f, quantidade_f, st.session_state.membro[0]['cpf']))
        for m in membros:
            uuid_pessoa = str(uuid.uuid4())
            pen.execute('''

            INSERT INTO Pessoas(uuid_pessoa, uuid_familia, nome, sexo, gestante, pcd, cpf, renda, data_nasc, telefone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uuid_pessoa, uuid_familia, m['nome'], m['sexo'], m['gestante'], m['pcd'], m['cpf'], m['renda'], m['data_nasc'], m['telefone']))
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