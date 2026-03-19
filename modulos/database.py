import sqlite3
import streamlit as st
import uuid
from geopy import Nominatim
import pandas as pd
from datetime import date
from .validacao import limpar_somente_numeros, limpar
from .calculos import calcular_indice_vulnerabilidade_familia, calcular_idade

def conexao_bd():
    return sqlite3.connect('Banco_dados.db')

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
            SELECT uuid_bairro, uuid_familia, tipo_moradia, custo_moradia, renda_familiar, COUNT(*) 
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
        
        resultados_membro = cur.fetchall()
        
        membro = []
        for row in resultados_membro:
            if isinstance(row, sqlite3.Row):
                membro.append(dict(row))
            else:
                colunas_m = [desc[0] for desc in cur.description]
                membro.append(dict(zip(colunas_m, row)))

        info_familia['membro'] = membro
        return info_familia

    finally:
        if conn_local:
            conn_local.close()

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

def novo_bairro(nome_b):
    if not nome_b:
        return

    conn = conexao_bd()

    bairros = [linha[0] for linha in conn.execute('SELECT nome_bairro FROM Bairros').fetchall()]
    conn.close()

    if limpar(nome_b) in [limpar(b) for b in bairros]:
        return nome_b.title()
    
    geolocator = Nominatim(user_agent="buscar_bairro")
    busca_b = f"{nome_b}, São Luis, MA, Brasil" 

    try:

        local = geolocator.geocode(busca_b, timeout=10)

        if local and ("São Luís" in local.address or "Sao Luis" in local.address):

            salvar_Bairro(nome_b, local)
            return  nome_b.title()   
    except Exception as e:
        print(f"Erro na API: {e}")
    
    return ""

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
            observacao TEXT,
            FOREIGN KEY (uuid_familia) REFERENCES Familias(uuid_familia)
                           )
            ''')

        

        conn.commit()
        conn.close()

def salvar_Familia(membro, bairro_f, moradia_f, custo_f, renda_f, quantidade_f, auxilio):

    uuid_familia = str(uuid.uuid4())
    conn = conexao_bd()
    pen = conn.cursor()

    pen.execute('SELECT uuid_bairro FROM Bairros WHERE nome_bairro = ?', (bairro_f.title(),))
    bairro_id_fet = pen.fetchone()
    bairro_id = bairro_id_fet[0]


    for m in membro:
         m['cpf'] = limpar_somente_numeros(m['cpf'])
         m['telefone'] = limpar_somente_numeros(m['telefone'])
    try:

        pen.execute('''

            INSERT INTO Familias(uuid_familia, uuid_bairro, tipo_moradia, custo_moradia, renda_familiar, cpf_responsavel, auxilio, ultima_visita)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uuid_familia, bairro_id, moradia_f, custo_f, renda_f, st.session_state.membro[0]['cpf'], auxilio, date.today().isoformat()))
        for m in membro:
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

    conn_local = None
    if cursor is None:
        conn_local = conexao_bd()
        cur = conn_local.cursor()
    else:
        cur = cursor

    try:
        # MODO INDIVIDUAL: Atualiza apenas uma família específica
        if uuid_familia:
            dados = dados_familia_calculo(uuid_familia, cursor=cur)
            
            if dados:
                if 'membros' not in dados and 'membro' in dados:
                    dados['membros'] = dados['membro']
                
                score = calcular_indice_vulnerabilidade_familia(dados)
                
                cur.execute("""
                    UPDATE Familias 
                    SET nivel_vulnerabilidade = ? 
                    WHERE uuid_familia = ?
                """, (score, uuid_familia))
                
                if conn_local:
                    conn_local.commit()
                
                return score
        
        # MODO MASSA: Atualiza TODAS as famílias
        else:
            
            # Busca todas as famílias
            cur.execute("SELECT uuid_familia FROM Familias")
            familias = cur.fetchall()
            
            atualizadas = 0
            erros = 0
            
            for i, (fam_id,) in enumerate(familias, 1):
                try:
                    dados = dados_familia_calculo(fam_id, cursor=cur)
                    
                    if dados:
                        # Ajusta para o formato esperado pela função de cálculo
                        if 'membros' not in dados and 'membro' in dados:
                            dados['membros'] = dados['membro']
                        
                        score = calcular_indice_vulnerabilidade_familia(dados)
                        
                        cur.execute("""
                            UPDATE Familias 
                            SET nivel_vulnerabilidade = ? 
                            WHERE uuid_familia = ?
                        """, (score, fam_id))
                        
                        atualizadas += 1
                    
                    # Progresso a cada 10 famílias
                    if i % 10 == 0:
                        if conn_local:
                            conn_local.commit()
                            
                except Exception as e:
                    erros += 1
                    print(f"Erro: {e}")
            
            if conn_local:
                conn_local.commit()
            
            return atualizadas
            
        return 0.0

    except Exception as e:
        if conn_local: 
            conn_local.rollback()
        print(f"Erro na atualização: {e}")
        return 0.0
    finally:
        if conn_local: 
            conn_local.close()

def atualizar_vulnerabilidade_bairro(uuid_bairro=None):
    conn = conexao_bd()
    cursor = conn.cursor()
    
    try:
        # MODO INDIVIDUAL: Atualiza apenas um bairro específico
        if uuid_bairro:
            lista_bairro = [(uuid_bairro,)]
        
        # MODO MASSA: Atualiza TODOS os bairros
        else:
            cursor.execute('SELECT uuid_bairro FROM Bairros')
            lista_bairro = cursor.fetchall()
        
        atualizados = 0
        for b in lista_bairro:
            uidd_bairro = b[0]

            cursor.execute('''
                SELECT AVG(nivel_vulnerabilidade) 
                FROM Familias 
                WHERE uuid_bairro = ?
            ''', (uidd_bairro,))
            
            resultado = cursor.fetchone()
            
            if resultado and resultado[0] is not None:
                media = round(resultado[0], 2)
            else:
                media = 0.0
                print(f"[!] Bairro {uidd_bairro} não possui famílias cadastradas.")
            
            cursor.execute('''
                UPDATE Bairros 
                SET nivel_vulnerabilidade = ? 
                WHERE uuid_bairro = ? 
            ''', (media, uidd_bairro))
            
            atualizados += 1
        
        conn.commit()
        
        return atualizados
        
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar bairros: {e}")
        return 0
    finally:
        conn.close()

def sincronizar_vulnerabilidades_completo():
    
    # Atualiza todas as famílias
    familias_atualizadas = atualizar_vulnerabilidades_familias()
    
    # Atualiza todos os bairros
    bairros_atualizados = atualizar_vulnerabilidade_bairro()
    
    return familias_atualizadas, bairros_atualizados

def pegar_totais():

    conn = conexao_bd()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM Familias')
    total_familias = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM Pessoas')
    resultado_pessoas = cursor.fetchone()[0]
    total_pessoas = resultado_pessoas if resultado_pessoas else 0
    
    conn.close()
    return total_familias, total_pessoas

def achar_responsavel(busca):
    conn = conexao_bd()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
                p.nome, 
                f.uuid_familia, 
                f.uuid_bairro,
                p.cpf, 
                f.renda_familiar,
                b.nome_bairro,
                f.cpf_responsavel,
                f.custo_moradia,
                f.auxilio,
                f.tipo_moradia
        FROM Familias f
        JOIN Pessoas p ON f.cpf_responsavel = p.cpf
        JOIN Bairros b ON f.uuid_bairro = b.uuid_bairro
        WHERE (p.nome LIKE ? OR p.cpf LIKE ?)
                    ''', (f'%{busca}%', f'%{busca}%'))
    resultado = cursor.fetchall()
    conn.commit()
    conn.close()

    return [dict(row) for row in resultado]

def achar_familia(uuid_familia):

    conn = conexao_bd()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
                   SELECT 
                            p.nome, 
                            p.sexo, 
                            p.gestante, 
                            p.data_nasc, 
                            p.pcd, 
                            p.renda, 
                            p.telefone, 
                            p.cpf, 
                            b.nome_bairro
                   FROM Pessoas p
                   JOIN Familias f ON p.uuid_familia = f.uuid_familia
                   JOIN Bairros b ON f.uuid_bairro = b.uuid_bairro
                   WHERE p.uuid_familia = ?''', (uuid_familia,))
    resultado = cursor.fetchall()
    
    conn.close()

    return [dict(row) for row in resultado]

def salvar_censo(dados_familia, lista_membro):

    try: 
        conn = conexao_bd()
        cursor = conn.cursor()

        if 'uuid_bairro' not in dados_familia:
            # Busque o uuid_bairro do banco ou use o bairro nome para encontrar
            cursor.execute('SELECT uuid_bairro FROM Bairros WHERE nome_bairro = ?', 
                        (dados_familia['bairro'],))
            resultado = cursor.fetchone()
            if resultado:
                dados_familia['uuid_bairro'] = resultado[0]

        id_f = dados_familia['uuid_familia']
        responsavel_final = dados_familia.get('novo_cpf_responsavel', dados_familia['cpf'])

        cursor.execute('''
            UPDATE Familias SET
                       uuid_bairro = ?,
                       custo_moradia = ?,
                       tipo_moradia = ?,
                       auxilio = ?,
                       cpf_responsavel = ?,
                       ultima_visita = ?
            WHERE uuid_familia = ?
        ''',(dados_familia.get('uuid_bairro'),
            float(dados_familia.get('custo_moradia', 0)),
            dados_familia.get('tipo_moradia'),
            int(dados_familia.get('auxilio', 0)),
            responsavel_final,
            date.today().isoformat(),
            id_f))
        
        renda_familiar = 0.0
        for m in lista_membro:
            if not isinstance(m, dict) : continue

            renda_familiar += float(m.get('renda', 0))

            d_nasc = m.get('data_nasc')
            if hasattr(d_nasc, 'isoformat'):
                d_nasc = d_nasc.isoformat()

            if m.get('is_novo_cadastro'):
                cursor.execute('''
                    INSERT INTO Pessoas (uuid_pessoa, uuid_familia, nome, sexo,
                                gestante, pcd, cpf, renda, data_nasc, telefone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (str(uuid.uuid4()), id_f, m['nome'], m['sexo'], int(m['gestante']), 
                      int(m['pcd']), m['cpf'], float(m['renda']), d_nasc, m['telefone']
                    ))

            else:

                cursor.execute('''
                        UPDATE Pessoas SET
                               renda = ?,
                               pcd = ?,
                               gestante = ?,
                               telefone = ?
                        WHERE cpf = ?
                    ''', (float(m['renda']), int(m['pcd']), int(m['gestante']), m['telefone'], m['cpf']))
        
        try:
            nivel_vulnerabilidade = atualizar_vulnerabilidades_familias(id_f, cursor=cursor)

        except Exception as e_calculo:
            print(f"Erro no cálculo: {e_calculo}")
            nivel_vulnerabilidade = "Erro no Cálculo"
        
        cursor.execute('''
            INSERT INTO Visitas (uuid_visita, uuid_familia, 
                                data_visita, auxilio, 
                                renda_no_momento, nivel_vulnerabilidade,
                                observacao)
            VALUES (?, ?, ?, ?, ?, ?, ? )
            ''',(str(uuid.uuid4()), id_f, date.today().isoformat(), 
                 int(dados_familia.get('auxilio', 0)), renda_familiar, nivel_vulnerabilidade,
                   dados_familia.get('observacao', '')
            ))
        
        conn.commit()
        return True
    
    except Exception as e:
        if conn: conn.rollback()
        print(f"Erro Detalhado: {e}")
        st.error(f"Erro ao salvar: {e}")
        return False
    finally:
        if conn: conn.close()

def carregar_dados_bairros():
    conn = conexao_bd()
    
    query = """
    WITH familias_com_pessoas AS (
        SELECT 
            f.uuid_bairro,
            f.uuid_familia,
            f.renda_familiar,
            COUNT(p.uuid_pessoa) as qtd_pessoas
        FROM Familias f
        LEFT JOIN Pessoas p ON f.uuid_familia = p.uuid_familia
        GROUP BY f.uuid_familia
    )
    SELECT 
        b.nome_bairro,
        b.nivel_vulnerabilidade as vulnerabilidade_atual,
        COUNT(DISTINCT f.uuid_familia) as total_familias,
        SUM(fcp.qtd_pessoas) as total_pessoas,
        COALESCE(SUM(CASE WHEN p.gestante = 1 THEN 1 ELSE 0 END), 0) as total_gestantes,
        COALESCE(SUM(CASE WHEN p.pcd = 1 THEN 1 ELSE 0 END), 0) as total_pcd,
        AVG(f.renda_familiar) as renda_media_familiar,
        AVG(f.renda_familiar / NULLIF(fcp.qtd_pessoas, 0)) as renda_per_capita_media
    FROM Bairros b
    LEFT JOIN Familias f ON b.uuid_bairro = f.uuid_bairro
    LEFT JOIN familias_com_pessoas fcp ON f.uuid_familia = fcp.uuid_familia
    LEFT JOIN Pessoas p ON f.uuid_familia = p.uuid_familia
    GROUP BY b.uuid_bairro, b.nome_bairro
    ORDER BY b.nivel_vulnerabilidade DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.fillna(0)

def carregar_evolucao_mensal():
    """Carrega dados de evolução mensal por bairro"""
    conn = conexao_bd()
    
    query = """
    SELECT 
        b.nome_bairro,
        strftime('%Y-%m', v.data_visita) as mes,
        COUNT(DISTINCT v.uuid_visita) as total_visitas,
        AVG(v.nivel_vulnerabilidade) as vulnerabilidade_media,
        AVG(v.renda_no_momento) as renda_media,
        SUM(v.auxilio) as total_auxilio
    FROM Visitas v
    JOIN Familias f ON v.uuid_familia = f.uuid_familia
    JOIN Bairros b ON f.uuid_bairro = b.uuid_bairro
    WHERE v.data_visita IS NOT NULL
    GROUP BY b.nome_bairro, strftime('%Y-%m', v.data_visita)
    ORDER BY mes DESC, b.nome_bairro
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def carregar_metricas_gerais():
    """Carrega métricas gerais do sistema"""
    conn = conexao_bd()
    
    query = """
    SELECT 
        COUNT(DISTINCT f.uuid_familia) as total_familias,
        COUNT(DISTINCT p.uuid_pessoa) as total_pessoas,
        AVG(f.nivel_vulnerabilidade) as vulnerabilidade_media_geral,
        COUNT(DISTINCT v.uuid_visita) as total_visitas,
        COUNT(DISTINCT CASE WHEN v.data_visita >= date('now', '-30 days') THEN v.uuid_visita END) as visitas_30d
    FROM Familias f
    LEFT JOIN Pessoas p ON f.uuid_familia = p.uuid_familia
    LEFT JOIN Visitas v ON f.uuid_familia = v.uuid_familia
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.iloc[0] if not df.empty else pd.Series()

def carregar_membros_familia(uuid_familia):
    conn = conexao_bd()
    query = """
    SELECT nome, sexo, gestante, pcd, renda, data_nasc, telefone, cpf
    FROM Pessoas WHERE uuid_familia = ?
    ORDER BY CASE WHEN cpf = (SELECT cpf_responsavel FROM Familias WHERE uuid_familia = ?) THEN 0 ELSE 1 END, data_nasc
    """
    df = pd.read_sql_query(query, conn, params=(uuid_familia, uuid_familia))
    conn.close()
    if not df.empty:
        df['idade'] = df['data_nasc'].apply(calcular_idade)
        df['faixa_etaria'] = df['idade'].apply(
            lambda x: 'Criança (0-12)' if x < 13 else ('Adolescente (13-17)' if x < 18 else ('Adulto (18-59)' if x < 60 else 'Idoso (60+)'))
        )
    return df

def carregar_todas_familias():
    conn = conexao_bd()
    query = """
    SELECT 
        f.uuid_familia, b.nome_bairro, f.tipo_moradia, f.custo_moradia,
        f.renda_familiar, f.auxilio, f.nivel_vulnerabilidade, f.ultima_visita,
        COUNT(p.uuid_pessoa) as qtd_membros,
        SUM(CASE WHEN p.gestante = 1 THEN 1 ELSE 0 END) as qtd_gestantes,
        SUM(CASE WHEN p.pcd = 1 THEN 1 ELSE 0 END) as qtd_pcd,
        (SELECT nome FROM Pessoas WHERE cpf = f.cpf_responsavel) as nome_responsavel,
        f.cpf_responsavel
    FROM Familias f
    JOIN Bairros b ON f.uuid_bairro = b.uuid_bairro
    LEFT JOIN Pessoas p ON f.uuid_familia = p.uuid_familia
    GROUP BY f.uuid_familia
    ORDER BY f.nivel_vulnerabilidade DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def carregar_estatisticas_gerais():
    conn = conexao_bd()
    query = """
    SELECT 
        COUNT(DISTINCT f.uuid_familia) as total_familias,
        COUNT(p.uuid_pessoa) as total_pessoas,
        AVG(f.nivel_vulnerabilidade) as vulnerabilidade_media,
        AVG(f.renda_familiar) as renda_media,
        COUNT(DISTINCT CASE WHEN f.auxilio = 1 THEN f.uuid_familia END) as familias_com_auxilio
    FROM Familias f
    LEFT JOIN Pessoas p ON f.uuid_familia = p.uuid_familia
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.iloc[0] if not df.empty else pd.Series()

