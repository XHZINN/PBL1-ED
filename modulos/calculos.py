from datetime import date, datetime

def calcular_idade(data_nasc):
    if not data_nasc:
        return 30
    
    # Garante que data_nasc seja um objeto date para o cálculo
    if isinstance(data_nasc, str):
        try:
            data_nasc = datetime.strptime(data_nasc, '%Y-%m-%d').date()
        except:  # noqa: E722
            return 30 # Idade padrão caso a string esteja errada

    hoje = date.today()
    return hoje.year - data_nasc.year - (
        (hoje.month, hoje.day) < (data_nasc.month, data_nasc.day)
    )
# -----------------------------
# INDICE DE VULNERABILIDADE DA FAMÍLIA
# -----------------------------
def calcular_indice_vulnerabilidade_familia(familia):

    if not familia or not familia.get('membro'):
        return 0.0

    membros = familia['membro']
    
    # Renda per capita
    renda_f = familia.get('renda_familiar', 0)
    qtd_pessoas = len(membros) if membros else 1
    renda_per_capita = renda_f / qtd_pessoas

    # --- PESO RENDA (0-4 pontos) ---
    if renda_per_capita <= 218:  # Extrema pobreza
        peso_renda = 4
    elif renda_per_capita <= 625:  # Pobreza
        peso_renda = 3
    elif renda_per_capita <= 1212:  # Baixa renda (2 salários mínimos)
        peso_renda = 2
    elif renda_per_capita <= 3030:  # Média renda (5 salários mínimos)
        peso_renda = 1
    else:  # Alta renda
        peso_renda = 0

    # --- PESO POR MEMBRO (0-7 pontos por membro) ---
    soma_pesos = 0
    for membro in membros:
        peso = 0
        idade = calcular_idade(membro["data_nasc"])
        
        # Peso por idade (0-3 pontos)
        if idade < 5 or idade >= 60:  # Crianças e idosos
            peso += 3
        elif idade <= 17:  # Adolescentes
            peso += 2
        else:  # Adultos
            peso += 1
        
        
        if int(membro.get("gestante", 0)):
            peso += 2
        if int(membro.get("pcd", 0)):
            peso += 2
            
        soma_pesos += peso

    
    media_pesos = soma_pesos / len(membros) if membros else 0

 
    indice_bruto = (peso_renda * 1.5) + (media_pesos * 1.2)
    
   
    indice_final = min(10, round(indice_bruto * 0.7, 2))

    return indice_final