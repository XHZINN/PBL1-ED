from datetime import date, datetime

def calcular_idade(data_nasc):
    if not data_nasc:
        return 0
    
    # Garante que data_nasc seja um objeto date para o cálculo
    if isinstance(data_nasc, str):
        try:
            data_nasc = datetime.strptime(data_nasc, '%Y-%m-%d').date()
        except:
            return 30 # Idade padrão caso a string esteja errada

    hoje = date.today()
    return hoje.year - data_nasc.year - (
        (hoje.month, hoje.day) < (data_nasc.month, data_nasc.day)
    )
# -----------------------------
# INDICE DE VULNERABILIDADE DA FAMÍLIA
# -----------------------------
def calcular_indice_vulnerabilidade_familia(familia):

    if not familia or not familia['membros']:
        return "N/A", 0.0

    membros = familia['membros']
    
    # gera a renda per capita da familia
    qtd_pessoas = familia['pessoas_familia'] if familia['pessoas_familia'] > 0 else 1
    renda_per_capita = familia['renda_familiar'] / qtd_pessoas

    # --- PESO RENDA SÃO LUÍS ---
    if renda_per_capita <= 218: 
        peso_renda = 4      # Extrema Pobreza
    elif renda_per_capita <= 520:
        peso_renda = 3      # Pobreza (Custo Cesta Básica SLZ)
    elif renda_per_capita <= 706: 
        peso_renda = 2      # Baixa Renda (1/2 Salário Mínimo)
    elif renda_per_capita <= 1412:
        peso_renda = 1.5    # Risco Moderado (1 Salário Mínimo)
    else:
        peso_renda = 1      # Vulnerabilidade Baixa

    soma_pesos_membros = 0

    for membro in membros:
        idade = calcular_idade(membro["data_nasc"])
        peso_individual = 0

        # Peso Idade
        if idade < 5:
            peso_individual += 3
        elif idade <= 17:
            peso_individual += 2
        elif idade >= 60:
            peso_individual += 3
        else:
            peso_individual += 1

        # Gestante
        if membro["gestante"]:
            peso_individual += 2

        # PCD
        if membro["pcd"]:
            peso_individual += 2

        soma_pesos_membros += peso_individual

    media_membros = soma_pesos_membros / len(membros)
    indice_bruto = peso_renda + media_membros

    # --- NORMALIZAÇÃO (0–10) ---
    indice_final = round(min(10, (indice_bruto / 11) * 10), 2)

    return membros[0]['nome'], indice_final

def calcular_indice_vulnerabilidade_bairro(dados_bairro):
   
    media = 0
    nivel_vulnerabilidade_total = 0
    
    for i in dados_bairro:
          nivel_vulnerabilidade_total += i

    media = nivel_vulnerabilidade_total / len(dados_bairro)
    
    return media