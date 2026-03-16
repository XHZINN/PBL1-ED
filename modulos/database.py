import sqlite3
import streamlit as st
import uuid
from geopy import Nominatim
from datetime import date, timedelta, datetime
import shutil
import os
from .validacao import limpar_somente_numeros, limpar
from .calculos import calcular_indice_vulnerabilidade_familia

def conexao_bd():
    return sqlite3.connect('Banco_dados.db')

def backup():

    last_data = buscar_data_backup()
    agora = datetime.now()
    hoje = agora.date()
    data_formatada = agora.strftime('%Y-%m-%d %H:%M:%S')

    if hoje <= last_data + timedelta(days=7):

        try:
            if not os.path.isdir('Backups'):
                os.makedirs("Backups")

            banco_dados = "Banco_dados.db"
            nome_backup = f"backup_{hoje}.db"

            path = os.path.join("Backups", nome_backup)

            shutil.copy2(banco_dados, path)
        

            conn = conexao_bd()
            cursor = conn.cursor()

            uuid_backup = str(uuid.uuid4())
            tipo = "Completo"

            cursor.execute('''
                INSERT INTO Backup(uuid_backup, nome_backup, caminho, data_criacao, tipo)
                VALUES (?, ?, ?, ?, ?)
                    ''', (uuid_backup, nome_backup, path, data_formatada, tipo))
            
            conn.commit()
            conn.close()

        except Exception as e:
             print(f'Erro ao salvar novo backup semanal: {e}')
             
def dados_familia_calculo(familia, cursor=None):
    # 1. Gerenciamento de Conexão Local ou Externa
    conn_local = None
    if cursor is None:
        conn_local = conexao_bd()
        conn_local.row_factory = sqlite3.Row
        cur = conn_local.cursor()
    else:
        cur = cursor

    try:
        # 2. Busca dados da Família
        cur.execute('''
            SELECT uuid_bairro, uuid_familia, tipo_moradia, custo_moradia, renda_familiar, pessoas_familia 
            FROM Familias 
            WHERE uuid_familia = ? 
        ''', (familia,))
        
        linha_familia = cur.fetchone()

        if not linha_familia:
            return None
        
        if isinstance(linha_familia, sqlite3.Row):
            info_familia = dict(linha_familia)
        else:
            
            colunas = [desc[0] for desc in cur.description]
            info_familia = dict(zip(colunas, linha_familia))
        
        cur.execute('''
            SELECT nome, gestante, pcd, data_nasc, renda
            FROM Pessoas
            WHERE uuid_familia = ?
        ''', (familia,))
        
        resultados_membros = cur.fetchall()
        
        membros = []
        for row in resultados_membros:
            if isinstance(row, sqlite3.Row):
                membros.append(dict(row))
            else:
                colunas_m = [desc[0] for desc in cur.description]
                membros.append(dict(zip(colunas_m, row)))

        info_familia['membros'] = membros
        return info_familia

    finally:
        if conn_local:
            conn_local.close()

def buscar_data_backup():
     
     try:
    
        conn = conexao_bd()
        cursor = conn.cursor()

        cursor.execute('SELECT data_criacao FROM Backup ORDER BY data_criacao DESC LIMIT 1')
        data = cursor.fetchone()
        conn.close()

        return datetime.strptime(data[0], '%Y-%m-%d').date() if data else date(2000, 1, 1)
     except Exception as e:
          return date(2000, 1, 1)
     
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

     cursor.execute('SELECT nome_bairro, latitude, longitude, nivel_vulnerabilidade FROM Bairros ORDER BY nome_bairro ASC')
     dados = cursor.fetchall()

     bairros = [{
          
          'bairro': linha[0],
          'lat': linha[1],
          'lon': linha[2],
          'intensidade': linha[3]
         }
        for linha in dados
     ]

     conn.close()
     return bairros
  
def query_relatorio():
     conn = conexao_bd()
     cursor = conn.cursor()

     cursor.execute('SELECT nome_bairro, nivel_vulnerabilidade FROM Bairros')
     bairros = cursor.fetchall

     cursor.execute('SELECT ')

def criar_table():
        conn = conexao_bd()
        trabaiador = conn.cursor()

        trabaiador.execute('''
        CREATE TABLE IF NOT EXISTS Bairros(
            uuid_bairro TEXT PRIMARY KEY NOT NULL,
            nome_bairro TEXT UNIQUE NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            nivel_vulnerabilidade REAL 
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
            auxilio INTEGER NOT NULL,
            nivel_vulnerabilidade REAL,
            ultima_visita DATE NOT NULL,
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

        trabaiador.execute('''
        CREATE TABLE IF NOT EXISTS Backup(
            
            uuid_backup TEXT PRIMARY KEY NOT NULL,
            nome_backup TEXT NOT NULL,
            caminho TEXT NOT NULL,
            data_criacao DATETIME NOT NULL,
            tipo TEXT              
                )
            ''')
        trabaiador.execute('''
        CREATE TABLE IF NOT EXISTS Visitas(
            uuid_visita TEXT PRIMARY KEY NOT NULL,
            uuid_familia TEXT NOT NULL,
            data_visita DATE NOT NULL,
            auxilio INTEGER NOT NULL,
            renda_no_momento REAL,
            nivel_vulnerabilidade REAL,
            FOREIGN KEY (uuid_familia) REFERENCES Familias(uuid_familia)
                           )
            ''')

        

        conn.commit()
        conn.close()

def salvar_Familia(membros, bairro_f, moradia_f, custo_f, renda_f, quantidade_f, auxilio):

    uuid_familia = str(uuid.uuid4())
    conn = conexao_bd()
    pen = conn.cursor()

    pen.execute('SELECT uuid_bairro FROM Bairros WHERE nome_bairro = ?', (bairro_f.title(),))
    bairro_id_fet = pen.fetchone()
    bairro_id = bairro_id_fet[0]


    for m in membros:
         m['cpf'] = limpar_somente_numeros(m['cpf'])
         m['telefone'] = limpar_somente_numeros(m['telefone'])
    try:

        pen.execute('''

            INSERT INTO Familias(uuid_familia, uuid_bairro, tipo_moradia, custo_moradia, renda_familiar, pessoas_familia, cpf_responsavel, auxilio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uuid_familia, bairro_id, moradia_f, custo_f, renda_f, quantidade_f, st.session_state.membro[0]['cpf'], auxilio))
        for m in membros:
            uuid_pessoa = str(uuid.uuid4())
            pen.execute('''

            INSERT INTO Pessoas(uuid_pessoa, uuid_familia, nome, sexo, gestante, pcd, cpf, renda, data_nasc, telefone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uuid_pessoa, uuid_familia, m['nome'], m['sexo'], m['gestante'], m['pcd'], m['cpf'], m['renda'], m['data_nasc'], m['telefone']))
        conn.commit()
        st.success("Família e Membros salvos com sucesso")

        atualizar_vulnerabilidades_familias(uuid_familia)

    except sqlite3.IntegrityError:
            st.error("Erro: Um dos CPFs já está cadastrado no sistema!")
    finally:
        conn.close()

def atualizar_vulnerabilidades_familias(uuid_familia=None, cursor=None):
    
    if cursor is None:
        conn = conexao_bd()
        cursor = conn.cursor()
    else:
        cur = cursor
    
    try:
        # Caso 1: Processamento Individual (Rapido)
        if uuid_familia:
            dados = dados_familia_calculo(uuid_familia, cursor=cur)
            
            uuid_bairro = None

            if dados:
                score, uuid_bairro = calcular_indice_vulnerabilidade_familia(dados)
                cur.execute("UPDATE Familias SET nivel_vulnerabilidade = ? WHERE uuid_familia = ?", (score, uuid_familia))

                if cursor is None:
                    conn.commit()   
                    conn.close()
                    atualizar_vulnerabilidade_bairro(uuid_bairro)
                return

        
        # Caso 2: Processo em Massa para todas as familias (Geral)
        cur.execute("SELECT uuid_familia FROM Familias")
        # Salva os dados na variavel familia como uma tupla
        todas_familia = cur.fetchall()

        for f in todas_familia:
            # 3. Busca os dados completos da família
            dados = dados_familia_calculo(f[0])
            
            if dados:
                score, _= calcular_indice_vulnerabilidade_familia(dados)
                
                # 4. Salva o resultado
                cur.execute("UPDATE Familias SET nivel_vulnerabilidade = ? WHERE uuid_familia = ?", (score, f[0]))
        if cursor is None:
            conn.commit()
            conn.close()
            atualizar_vulnerabilidade_bairro(None)

    except Exception as e:
        # Se deu erro e a conexão é local, desfaz
        if cursor is None:
            conn.rollback()
            conn.close()
        raise e # Rebola o erro para o registrar_visita saber que falhou

def atualizar_vulnerabilidade_bairro(uuid_bairro=None):
     
    conn = conexao_bd()
    cursor = conn.cursor()

    if uuid_bairro:
        lista_bairro = [(uuid_bairro,)]

    else:
        # 1. Pega os dados brutos de todos os bairros
        cursor.execute('SELECT uuid_bairro FROM Bairros')

        # 2. Salva os dados na variavel bairros
        lista_bairro = cursor.fetchall()

    for b in lista_bairro:
        
        uidd_bairro = b[0]

        cursor.execute('''
                    SELECT AVG(nivel_vulnerabilidade) 
                    FROM Familias 
                    WHERE uuid_bairro = ?
                    ''', (uidd_bairro,))
        resultado = cursor.fetchone()

        media = round(resultado[0] if resultado[0] is not None else 0.0, 2)

        cursor.execute('''
                    UPDATE Bairros 
                    SET nivel_vulnerabilidade = ? 
                    WHERE uuid_bairro = ? 
                    ''', (media, uidd_bairro))

    conn.commit()
    conn.close
    
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

def registrar_visita(uuid_familia, lista_membros, renda_total, recebeu_auxilio, obs):
    conn = conexao_bd()
    cursor = conn.cursor()
    
    agora = datetime.now()
    data_formatada = agora.strftime('%Y-%m-%d')
    timestamp = agora.strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # 1. ATUALIZAR CADA MEMBRO (Indivíduos)
        for m in lista_membros:
            cursor.execute('''
                UPDATE Pessoas 
                SET renda = ?, gestante = ?, pcd = ?
                WHERE cpf = ? AND uuid_familia = ?
            ''', (m['renda'], m['gestante'], m['pcd'], m['cpf'], uuid_familia))

        # 2. ATUALIZAR A FAMÍLIA (Dados Agregados)
        cursor.execute('''
            UPDATE Familias 
            SET renda_familiar = ?, ultima_visita = ?, auxilio =?
            WHERE uuid_familia = ?
        ''', (renda_total, data_formatada, recebeu_auxilio, uuid_familia))

        atualizar_vulnerabilidades_familias(uuid_familia, cursor=cursor)

        # 3. INSERIR NO HISTÓRICO DE VISITAS (Snapshot imutável)
        # Usamos o timestamp completo para o histórico ser preciso
        cursor.execute('''
            INSERT INTO Visitas (
                uuid_visita, uuid_familia, data_visita, 
                auxilio, renda_no_momento, observacao
            ) VALUES (LOWER(HEX(RANDOMBLOB(16))), ?, ?, ?, ?, ?)
        ''', (uuid_familia, timestamp, recebeu_auxilio, renda_total, obs))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro na transação: {e}")
        return False
    finally:
        conn.close()

def buscar_responsavel_por_cpf_ou_nome(termo_busca):
    """Busca o responsável pelo CPF ou Nome para iniciar uma visita."""
    conn = conexao_bd()
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # Ajustado: Filtramos pessoas que possuem o CPF igual ao cpf_responsavel da familia
    query = """
        SELECT 
            f.uuid_familia, 
            p.nome, 
            p.cpf,
            f.renda_familiar, 
            b.nome_bairro,
            f.cpf_responsavel
        FROM Familias f
        JOIN Pessoas p ON f.cpf_responsavel = p.cpf
        JOIN Bairros b ON f.uuid_bairro = b.uuid_bairro
        WHERE (p.nome LIKE ? OR p.cpf LIKE ?)
    """
    
    params = (f'%{termo_busca}%', f'%{termo_busca}%')
    cursor.execute(query, params)
    resultados = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in resultados]

def buscar_membros_familia(uuid_familia):
    conn = conexao_bd()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM Pessoas WHERE uuid_familia = ?", (uuid_familia,))
    membros = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return membros


