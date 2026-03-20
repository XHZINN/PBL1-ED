import sqlite3
import uuid
import random
from datetime import timedelta, date
from faker import Faker

# Inicializa o gerador configurado para o português do Brasil
fake = Faker('pt_BR')

# Lista de bairros reais de São Luís para garantir dados consistentes

def conexao_bd():
    """Conecta ao banco de dados SQLite"""
    return sqlite3.connect("Banco_dados.db")

def gerar_cpf_valido():
    """Gera um CPF válido aleatório sem formatação (apenas números)"""
    digitos = [random.randint(0, 9) for _ in range(9)]
    
    while len(set(digitos)) == 1:
        digitos = [random.randint(0, 9) for _ in range(9)]
    
    # Calcula primeiro dígito verificador
    soma = sum(digitos[i] * (10 - i) for i in range(9))
    digito1 = (soma * 10) % 11
    digito1 = 0 if digito1 >= 10 else digito1
    digitos.append(digito1)
    
    # Calcula segundo dígito verificador
    soma = sum(digitos[i] * (11 - i) for i in range(10))
    digito2 = (soma * 10) % 11
    digito2 = 0 if digito2 >= 10 else digito2
    digitos.append(digito2)
    
    return ''.join(map(str, digitos))

def gerar_telefone():
    """Gera um telefone do Maranhão (98 ou 99)"""
    ddd = random.choice(["98", "99"])
    numero = f"{random.randint(9, 9)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
    return f"{ddd}{numero}"

def gerar_data_nasc(tipo):
    """
    Gera data de nascimento baseada no tipo
    """
    hoje = date.today()
    
    if tipo == "crianca":
        idade = random.randint(0, 12)
    elif tipo == "adolescente":
        idade = random.randint(13, 17)
    elif tipo == "idoso":
        idade = random.randint(60, 90)
    else:  # adulto
        idade = random.randint(18, 59)
    
    data = hoje - timedelta(days=idade*365 + random.randint(0, 365))
    return data.isoformat()


def criar_visitas_historicas(uuid_familia, cursor, meses=12):
    """Cria visitas históricas para uma família - CORRIGIDO"""
    hoje = date.today()
    
    for i in range(meses):
        data_visita = hoje - timedelta(days=30 * i + random.randint(-5, 5))
        
        # Busca dados atuais da família
        cursor.execute('''
            SELECT renda_familiar, nivel_vulnerabilidade FROM Familias WHERE uuid_familia = ?
        ''', (uuid_familia,))
        result = cursor.fetchone()
        if not result:
            continue
            
        renda_atual, vuln_atual = result
        
        # Gera variação nos dados históricos
        renda_historica = renda_atual * random.uniform(0.7, 1.3)
        vuln_historica = vuln_atual * random.uniform(0.8, 1.2)
        vuln_historica = min(10, max(0, vuln_historica))  # Limita entre 0-10
        auxilio_historico = 1 if random.random() < 0.4 else 0
        
        uuid_visita = str(uuid.uuid4())
        try:
            cursor.execute('''
                INSERT INTO Visitas (uuid_visita, uuid_familia, data_visita, 
                                   auxilio, renda_no_momento, nivel_vulnerabilidade, observacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (uuid_visita, uuid_familia, data_visita.isoformat(), 
                  auxilio_historico, round(renda_historica, 2), 
                  round(vuln_historica, 2),
                  fake.sentence(nb_words=8)))
        except sqlite3.IntegrityError:
            continue

def semear_dados(qtd_familias=100):
    """
    Função principal para semear o banco de dados
    """
    print(f"[*] Iniciando semeadura de {qtd_familias} famílias...")
    
    conn = conexao_bd()
    cursor = conn.cursor()
    
  
    # Busca bairros
    cursor.execute("SELECT uuid_bairro, nome_bairro FROM Bairros")
    bairros = cursor.fetchall()
    
    if not bairros:
        print("[-] Erro: Nenhum bairro encontrado!")
        return
    
    cpfs_utilizados = set()
    
    for familia_idx in range(qtd_familias):
        # Seleciona bairro
        bairro = random.choices(
            bairros,
            weights=[_get_peso_bairro(b[1]) for b in bairros]
        )[0]
        
        u_bairro, nome_bairro = bairro
        perfil = _get_perfil_bairro(nome_bairro)
        
        # Gera dados da família
        uuid_familia = str(uuid.uuid4())
        
        # Quantidade de pessoas
        if perfil == "critico":
            qtd_pessoas = random.randint(4, 8)
            renda_familia = round(random.uniform(300, 1500), 2)
            auxilio = 1 if random.random() < 0.7 else 0
            tipo_moradia = random.choices(
                ["Ocupação", "Aluguel", "Cedida", "Casa Própria"],
                weights=[0.3, 0.4, 0.2, 0.1]
            )[0]
        elif perfil == "estavel":
            qtd_pessoas = random.randint(1, 4)
            renda_familia = round(random.uniform(5000, 20000), 2)
            auxilio = 0
            tipo_moradia = random.choices(
                ["Casa Própria", "Aluguel", "Cedida"],
                weights=[0.7, 0.25, 0.05]
            )[0]
        else:  # medio
            qtd_pessoas = random.randint(2, 5)
            renda_familia = round(random.uniform(1500, 5000), 2)
            auxilio = 1 if random.random() < 0.3 else 0
            tipo_moradia = random.choices(
                ["Aluguel", "Casa Própria", "Cedida"],
                weights=[0.5, 0.4, 0.1]
            )[0]
        
        # Custo moradia
        if tipo_moradia == "Aluguel":
            custo_moradia = round(renda_familia * random.uniform(0.2, 0.4), 2)
        else:
            custo_moradia = 0
        
        # CPF responsável
        while True:
            cpf_resp = gerar_cpf_valido()
            if cpf_resp not in cpfs_utilizados:
                cpfs_utilizados.add(cpf_resp)
                break
        
        # Data última visita
        ultima_visita = (date.today() - timedelta(days=random.randint(0, 90))).isoformat()
        
        # Insere família (sem nivel_vulnerabilidade ainda)
        try:
            cursor.execute('''
                INSERT INTO Familias (uuid_familia, uuid_bairro, tipo_moradia, 
                                     custo_moradia, renda_familiar, cpf_responsavel, 
                                     auxilio, ultima_visita, nivel_vulnerabilidade)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uuid_familia, u_bairro, tipo_moradia, custo_moradia, 
                  renda_familia, cpf_resp, auxilio, ultima_visita, 0.0))
        except sqlite3.IntegrityError:
            print(f"[-] Erro ao inserir família {familia_idx+1}, pulando...")
            continue
        
        # Cria membros
        for i in range(qtd_pessoas):
            uuid_pessoa = str(uuid.uuid4())
            
            if i == 0:  # Responsável
                nome = fake.name()
                cpf = cpf_resp
                renda = renda_familia
                tipo_pessoa = "adulto"
            else:
                while True:
                    cpf = gerar_cpf_valido()
                    if cpf not in cpfs_utilizados:
                        cpfs_utilizados.add(cpf)
                        break
                
                # Tipo da pessoa
                if i < qtd_pessoas - 1:
                    tipo_pessoa = random.choices(
                        ["crianca", "adolescente", "adulto", "idoso"],
                        weights=[0.4, 0.2, 0.3, 0.1]
                    )[0]
                else:
                    tipo_pessoa = random.choice(["adulto", "idoso"])
                
                nome = fake.name()
                renda = 0
            
            # Características
            sexo = random.choice(["Masculino", "Feminino"])
            
            if sexo == "Feminino" and tipo_pessoa in ["adulto", "adolescente"]:
                gestante = 1 if random.random() < 0.15 else 0
            else:
                gestante = 0
            
            pcd = 1 if random.random() < 0.05 else 0
            telefone = gerar_telefone() if random.random() < 0.7 else ""
            
            try:
                cursor.execute('''
                    INSERT INTO Pessoas (uuid_pessoa, uuid_familia, nome, sexo, 
                                       gestante, pcd, cpf, renda, data_nasc, telefone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (uuid_pessoa, uuid_familia, nome, sexo, gestante, pcd, 
                      cpf, renda, gerar_data_nasc(tipo_pessoa), telefone))
            except sqlite3.IntegrityError:
                continue
        
        # Commit a cada 10 famílias
        if (familia_idx + 1) % 10 == 0:
            conn.commit()
            print(f"[*] {familia_idx + 1}/{qtd_familias} famílias processadas...")
    
    conn.commit()
    print("[*] Famílias inseridas. Calculando vulnerabilidades...")
    
    # ===== CALCULA VULNERABILIDADES =====
    from modulos.calculos import calcular_indice_vulnerabilidade_familia
    from modulos.database import dados_familia_calculo
    
    cursor.execute("SELECT uuid_familia FROM Familias")
    familias = cursor.fetchall()
    
    for idx, (fam_id,) in enumerate(familias):
        try:
            dados = dados_familia_calculo(fam_id, cursor=cursor)
            if dados:
                # Ajusta para o formato esperado
                if 'membros' not in dados and 'membro' in dados:
                    dados['membros'] = dados['membro']
                
                indice = calcular_indice_vulnerabilidade_familia(dados)
                
                # Atualiza família
                cursor.execute('''
                    UPDATE Familias SET nivel_vulnerabilidade = ? 
                    WHERE uuid_familia = ?
                ''', (indice, fam_id))
                
                # Cria visitas históricas com o índice calculado
                criar_visitas_historicas(fam_id, cursor, meses=12)
                
            if (idx + 1) % 20 == 0:
                conn.commit()
                print(f"[*] {idx + 1}/{len(familias)} vulnerabilidades calculadas...")
                
        except Exception as e:
            print(f"[-] Erro ao calcular vulnerabilidade da família {fam_id}: {e}")
            continue
    
    conn.commit()
    
    # Atualiza vulnerabilidade dos bairros
    print("[*] Atualizando vulnerabilidade dos bairros...")
    cursor.execute('''
        UPDATE Bairros 
        SET nivel_vulnerabilidade = (
            SELECT AVG(nivel_vulnerabilidade) 
            FROM Familias 
            WHERE Familias.uuid_bairro = Bairros.uuid_bairro
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"[+] Semeadura concluída! {qtd_familias} famílias criadas.")
    print("[+] Visitas históricas criadas para análises mensais.")

def _get_peso_bairro(nome_bairro):
    """Retorna peso para seleção aleatória de bairros"""
    bairros_criticos = ["Coroadinho", "Vila Luizão", "Cidade Operária", "Anjo da Guarda", "Liberdade"]
    bairros_nobres = ["Renascença", "Ponta d'Areia", "Calhau", "São Francisco", "Jardim Renascença"]
    
    if nome_bairro in bairros_criticos:
        return 2.0
    elif nome_bairro in bairros_nobres:
        return 0.5
    else:
        return 1.0

def _get_perfil_bairro(nome_bairro):
    """Retorna o perfil socioeconômico do bairro"""
    bairros_criticos = ["Coroadinho", "Vila Luizão", "Cidade Operária", "Anjo da Guarda", "Liberdade"]
    bairros_nobres = ["Renascença", "Ponta d'Areia", "Calhau", "São Francisco", "Jardim Renascença"]
    
    if nome_bairro in bairros_criticos:
        return "critico"
    elif nome_bairro in bairros_nobres:
        return "estavel"
    else:
        return "medio"

if __name__ == "__main__":
    try:
        qtd = int(input("Quantas famílias deseja gerar? (padrão: 100): ") or "100")
        semear_dados(qtd)
    except ValueError:
        print("Valor inválido. Usando padrão de 100 famílias.")
        semear_dados(100)