import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
from datetime import datetime
import os
from modulos.database import carregar_dados_bairros, carregar_evolucao_mensal,carregar_metricas_gerais


# Configurar matplotlib
plt.rcParams['axes.unicode_minus'] = False

def gerar_graficos_analise(df_bairros, df_evolucao_mensal):
    """Gera todos os gráficos para o relatório"""
    
    # Configurar estilo
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. Distribuição da vulnerabilidade
    plt.figure(figsize=(12, 6))
    sns.histplot(df_bairros['vulnerabilidade_atual'], bins=15, kde=True, color='#2E4057')
    media_vuln = df_bairros['vulnerabilidade_atual'].mean()
    plt.axvline(media_vuln, color='red', linestyle='--', 
                label=f"Média: {media_vuln:.2f}")
    plt.title('Distribuição do Índice de Vulnerabilidade em São Luís', 
              fontsize=16, fontweight='bold')
    plt.xlabel('Índice de Vulnerabilidade (0-10)', fontsize=12)
    plt.ylabel('Quantidade de Bairros', fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig('relatorio_distribuicao.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 2. Top 15 bairros mais críticos
    plt.figure(figsize=(12, 8))
    top_v = df_bairros.nlargest(15, 'vulnerabilidade_atual')
    cores = sns.color_palette("Reds_r", len(top_v))
    bars = plt.barh(range(len(top_v)), top_v['vulnerabilidade_atual'].values, color=cores)
    plt.yticks(range(len(top_v)), top_v['nome_bairro'].values)
    plt.xlabel('Índice de Vulnerabilidade', fontsize=12)
    plt.title('Top 15 Bairros com Maior Vulnerabilidade', fontsize=16, fontweight='bold')
    
    for i, (bar, val) in enumerate(zip(bars, top_v['vulnerabilidade_atual'].values)):
        plt.text(val + 0.1, bar.get_y() + bar.get_height()/2, f'{val:.2f}', 
                va='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('relatorio_top_criticos.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 3. Gráfico de pizza - Composição populacional
    plt.figure(figsize=(10, 8))
    total_pessoas = df_bairros['total_pessoas'].sum()
    total_gestantes = df_bairros['total_gestantes'].sum()
    total_pcd = df_bairros['total_pcd'].sum()
    
    labels = ['População Geral', 'Gestantes', 'PCDs']
    sizes = [total_pessoas, total_gestantes, total_pcd]
    colors = ['#66b3ff', '#ffcc99', '#ff9999']
    explode = (0, 0.1, 0.1)
    
    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90, textprops={'fontsize': 12})
    plt.title('Composição da População Acompanhada', fontsize=16, fontweight='bold')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('relatorio_composicao.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 4. Evolução mensal (se houver dados)
    if not df_evolucao_mensal.empty:
        plt.figure(figsize=(14, 7))
        
        # Pega os 5 bairros com mais dados
        top5_bairros = df_evolucao_mensal.groupby('nome_bairro')['vulnerabilidade_media'].mean().nlargest(5).index
        df_plot = df_evolucao_mensal[df_evolucao_mensal['nome_bairro'].isin(top5_bairros)]
        
        for bairro in top5_bairros:
            df_bairro = df_plot[df_plot['nome_bairro'] == bairro].sort_values('mes')
            plt.plot(df_bairro['mes'], df_bairro['vulnerabilidade_media'], 
                    marker='o', linewidth=2, label=bairro)
        
        plt.title('Evolução Mensal da Vulnerabilidade - Top 5 Bairros Críticos', 
                  fontsize=16, fontweight='bold')
        plt.xlabel('Mês/Ano', fontsize=12)
        plt.ylabel('Índice de Vulnerabilidade', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend(loc='upper right', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('relatorio_evolucao_mensal.png', dpi=150, bbox_inches='tight')
        plt.close()

    # 5. Distribuição por categoria de risco
    plt.figure(figsize=(12, 6))
    
    bins = [0, 3, 6, 8, 10]
    labels = ['Baixo (0-3)', 'Médio (3-6)', 'Alto (6-8)', 'Crítico (8-10)']
    df_bairros['categoria'] = pd.cut(df_bairros['vulnerabilidade_atual'], bins=bins, labels=labels)
    
    categoria_counts = df_bairros['categoria'].value_counts().sort_index()
    
    plt.bar(categoria_counts.index, categoria_counts.values, 
            color=['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c'])
    plt.title('Distribuição dos Bairros por Nível de Vulnerabilidade', 
              fontsize=16, fontweight='bold')
    plt.xlabel('Categoria', fontsize=12)
    plt.ylabel('Quantidade de Bairros', fontsize=12)
    
    for i, (idx, val) in enumerate(categoria_counts.items()):
        plt.text(i, val + 0.1, str(val), ha='center', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('relatorio_categorias.png', dpi=150, bbox_inches='tight')
    plt.close()

def criar_pdf_relatorio(df_bairros, df_evolucao_mensal, metricas):
    """Cria o PDF do relatório usando os dados carregados"""
    
    # Gerar gráficos
    gerar_graficos_analise(df_bairros, df_evolucao_mensal)
    
    # Inicializar PDF com suporte a UTF-8
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # ===== PÁGINA 1 =====
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font('Arial', 'B', 20)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 20, 'RELATÓRIO DE VULNERABILIDADE SOCIAL', 0, 1, 'C')
    pdf.set_font('Arial', 'I', 12)
    pdf.set_text_color(52, 73, 94)
    pdf.cell(0, 10, 'São Luís - MA', 0, 1, 'C')
    pdf.cell(0, 10, f'Data de emissão: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
    pdf.ln(10)
    
    # Resumo executivo
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 10, '1. RESUMO EXECUTIVO', 0, 1, 'L')
    pdf.ln(5)
    
    total_familias = int(metricas.get('total_familias', 0))
    total_pessoas = int(metricas.get('total_pessoas', 0))
    media_vuln = metricas.get('vulnerabilidade_media_geral', 0)
    total_visitas = int(metricas.get('total_visitas', 0))
    visitas_30d = int(metricas.get('visitas_30d', 0))
    bairros_criticos = len(df_bairros[df_bairros['vulnerabilidade_atual'] >= 8])
    
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    
    texto_resumo = [
        f"Este relatório apresenta a análise de {len(df_bairros)} bairros do município de São Luís, ",
        f"abrangendo {total_familias:,} famílias e {total_pessoas:,} pessoas acompanhadas pelo programa.",
        "",
        "INDICADORES GERAIS:",
        f"- Índice médio de vulnerabilidade: {media_vuln:.2f}",
        f"- Bairros em situação crítica (≥8): {bairros_criticos}",
        f"- Total de gestantes identificadas: {int(df_bairros['total_gestantes'].sum())}",
        f"- Total de PCDs identificados: {int(df_bairros['total_pcd'].sum())}",
        f"- Total de visitas realizadas: {total_visitas}",
        f"- Visitas nos últimos 30 dias: {visitas_30d}",
        "",
        "Os dados foram coletados através de visitas técnicas e atualizações cadastrais ",
        "realizadas pela equipe de assistência social do município."
    ]
    
    for linha in texto_resumo:
        # Converter para latin-1 com substituição de caracteres não suportados
        try:
            linha_encoded = linha.encode('latin-1', errors='replace').decode('latin-1')
            pdf.multi_cell(0, 7, linha_encoded)
        except:
            pdf.multi_cell(0, 7, linha)
    
    pdf.ln(10)
    
    # ===== PÁGINA 2 - GRÁFICOS =====
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '2. ANÁLISE GRÁFICA', 0, 1, 'L')
    pdf.ln(5)
    
    # Distribuição
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2.1 Distribuição da Vulnerabilidade', 0, 1, 'L')
    pdf.image('relatorio_distribuicao.png', x=10, w=190)
    pdf.ln(5)
    
    # Composição
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2.2 Composição da População', 0, 1, 'L')
    pdf.image('relatorio_composicao.png', x=30, w=150)
    pdf.ln(5)
    
    # ===== PÁGINA 3 - MAIS GRÁFICOS =====
    pdf.add_page()
    
    # Top críticos
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2.3 Ranking de Bairros Críticos', 0, 1, 'L')
    pdf.image('relatorio_top_criticos.png', x=10, w=190)
    pdf.ln(5)
    
    # Categorias
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2.4 Classificação por Nível de Risco', 0, 1, 'L')
    pdf.image('relatorio_categorias.png', x=10, w=190)
    
    # ===== PÁGINA 4 - EVOLUÇÃO MENSAL =====
    if not df_evolucao_mensal.empty:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, '3. EVOLUÇÃO TEMPORAL', 0, 1, 'L')
        pdf.ln(5)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '3.1 Evolução Mensal da Vulnerabilidade', 0, 1, 'L')
        pdf.image('relatorio_evolucao_mensal.png', x=10, w=190)
        pdf.ln(10)
        
        # Tabela resumo mensal
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '3.2 Resumo por Mês', 0, 1, 'L')
        
        resumo_mensal = df_evolucao_mensal.groupby('mes').agg({
            'vulnerabilidade_media': 'mean',
            'total_visitas': 'sum',
            'total_auxilio': 'sum'
        }).round(2).reset_index().sort_values('mes', ascending=False).head(12)
        
        # Cabeçalho da tabela
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(35, 8, 'Mês/Ano', 1, 0, 'C', True)
        pdf.cell(35, 8, 'Vulnerab.', 1, 0, 'C', True)
        pdf.cell(35, 8, 'Visitas', 1, 0, 'C', True)
        pdf.cell(35, 8, 'Auxílios', 1, 1, 'C', True)
        
        # Dados da tabela
        pdf.set_font('Arial', '', 8)
        for _, row in resumo_mensal.iterrows():
            pdf.cell(35, 7, str(row['mes']), 1, 0, 'C')
            pdf.cell(35, 7, f"{row['vulnerabilidade_media']:.2f}", 1, 0, 'C')
            pdf.cell(35, 7, str(int(row['total_visitas'])), 1, 0, 'C')
            pdf.cell(35, 7, str(int(row['total_auxilio'])), 1, 1, 'C')
    
    # ===== PÁGINA 5 - TABELA COMPLETA =====
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '4. TABELA COMPLETA DE DADOS', 0, 1, 'L')
    pdf.ln(5)
    
    # Cabeçalho da tabela
    pdf.set_font('Arial', 'B', 8)
    pdf.set_fill_color(220, 220, 220)
    
    colunas = ['Bairro', 'Índice', 'Famílias', 'Pessoas', 'Gest.', 'PCDs', 'Renda Média']
    larguras = [60, 18, 20, 20, 15, 15, 32]
    
    for i, col in enumerate(colunas):
        # Converter título da coluna
        try:
            col_encoded = col.encode('latin-1', errors='replace').decode('latin-1')
            pdf.cell(larguras[i], 8, col_encoded, 1, 0, 'C', True)
        except:
            pdf.cell(larguras[i], 8, col, 1, 0, 'C', True)
    pdf.ln()
    
    # Linhas da tabela
    pdf.set_font('Arial', '', 7)
    df_ordenado = df_bairros.sort_values('vulnerabilidade_atual', ascending=False)
    
    for idx, (_, row) in enumerate(df_ordenado.iterrows()):
        if pdf.get_y() > 260:
            pdf.add_page()
            # Repetir cabeçalho
            pdf.set_font('Arial', 'B', 8)
            for i, col in enumerate(colunas):
                try:
                    col_encoded = col.encode('latin-1', errors='replace').decode('latin-1')
                    pdf.cell(larguras[i], 8, col_encoded, 1, 0, 'C', True)
                except:
                    pdf.cell(larguras[i], 8, col, 1, 0, 'C', True)
            pdf.ln()
            pdf.set_font('Arial', '', 7)
        
        # Cor de fundo alternada
        pdf.set_fill_color(245, 245, 245) if idx % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        
        # Nome do bairro
        nome_bairro = str(row['nome_bairro'])[:30]
        try:
            nome_encoded = nome_bairro.encode('latin-1', errors='replace').decode('latin-1')
            pdf.cell(larguras[0], 6, nome_encoded, 1, 0, 'L', True)
        except:
            pdf.cell(larguras[0], 6, nome_bairro, 1, 0, 'L', True)
        
        pdf.cell(larguras[1], 6, f"{row['vulnerabilidade_atual']:.2f}", 1, 0, 'C', True)
        pdf.cell(larguras[2], 6, str(int(row['total_familias'])), 1, 0, 'C', True)
        pdf.cell(larguras[3], 6, str(int(row['total_pessoas'])), 1, 0, 'C', True)
        pdf.cell(larguras[4], 6, str(int(row['total_gestantes'])), 1, 0, 'C', True)
        pdf.cell(larguras[5], 6, str(int(row['total_pcd'])), 1, 0, 'C', True)
        
        renda_text = f"R$ {row['renda_media_familiar']:,.2f}" if row['renda_media_familiar'] > 0 else "N/D"
        try:
            renda_encoded = renda_text.encode('latin-1', errors='replace').decode('latin-1')
            pdf.cell(larguras[6], 6, renda_encoded, 1, 1, 'R', True)
        except:
            pdf.cell(larguras[6], 6, renda_text, 1, 1, 'R', True)
    
    # Rodapé
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 5, 'Relatório gerado automaticamente pelo Sistema de Monitoramento Social de São Luís', 0, 1, 'C')
    
    # Salvar PDF
    nome_arquivo = f'Relatorio_Sao_Luis_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    pdf.output(nome_arquivo)
    
    # Limpar arquivos temporários
    for arquivo in ['relatorio_distribuicao.png', 'relatorio_top_criticos.png', 
                   'relatorio_composicao.png', 'relatorio_evolucao_mensal.png', 
                   'relatorio_categorias.png']:
        if os.path.exists(arquivo):
            os.remove(arquivo)
    
    return nome_arquivo

def gerar_relatorio():
    """Função principal para gerar o relatório"""
    
    # Carregar dados
    print("[1/4] Carregando dados dos bairros...")
    df_bairros = carregar_dados_bairros()
    
    print("[2/4] Carregando dados de evolução mensal...")
    df_evolucao = carregar_evolucao_mensal()
    
    print("[3/4] Carregando métricas gerais...")
    metricas = carregar_metricas_gerais()
    
    # Gerar relatório
    print("[4/4] Gerando PDF...")
    nome_arquivo = criar_pdf_relatorio(df_bairros, df_evolucao, metricas)
    
    # Resumo
    print("\n" + "="*60)
    print("RELATÓRIO GERADO COM SUCESSO!")
    print("="*60)
    print(f"Arquivo: {nome_arquivo}")
    print(f"Bairros analisados: {len(df_bairros)}")
    print(f"Famílias: {int(metricas.get('total_familias', 0)):,}".replace(',', '.'))
    print(f"Pessoas: {int(metricas.get('total_pessoas', 0)):,}".replace(',', '.'))
    print(f"Vulnerabilidade média: {metricas.get('vulnerabilidade_media_geral', 0):.2f}")
    print(f"Total de visitas: {int(metricas.get('total_visitas', 0))}")
    print("="*60)
    
    return nome_arquivo