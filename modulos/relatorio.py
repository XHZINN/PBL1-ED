import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
from modulos.database import conexao_bd

def gerar_elementos_visuais(df):
    """Gera gráficos baseados em todos os bairros cadastrados."""
    plt.figure(figsize=(10, 6))
    sns.histplot(df['Vulnerabilidade Bairro'], bins=10, kde=True, color='darkred')
    plt.title('Distribuição do Índice de Vulnerabilidade em São Luís')
    plt.xlabel('Índice (0 a 10)')
    plt.ylabel('Quantidade de Bairros')
    plt.savefig('panorama_geral.png', bbox_inches='tight', dpi=150)
    plt.close()

    plt.figure(figsize=(10, 8))
    top_v = df.sort_values('Vulnerabilidade Bairro', ascending=False).head(15)
    sns.barplot(x='Vulnerabilidade Bairro', y='Bairro', data=top_v, palette='flare')
    plt.title('Top 15 Bairros com Maior Vulnerabilidade')
    plt.savefig('top_criticos.png', bbox_inches='tight', dpi=150)
    plt.close()

class PDFRelatorio(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(150, 0, 0)
        self.cell(0, 10, 'RELATÓRIO CONSOLIDADO DE VULNERABILIDADE SOCIAL', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, 'Análise de Indicadores Socioeconômicos por Bairro - São Luís/MA', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def criar_pdf_completo(df):
    pdf = PDFRelatorio()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PÁGINA 1: CAPA E GRÁFICOS ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '1. Análise Estatística Geral', 0, 1)
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 11)
    texto_intro = (f"Este relatório contempla a análise de {len(df)} bairros. "
                   f"A média geral de vulnerabilidade do município é de {df['Vulnerabilidade Bairro'].mean():.2f}. "
                   "Abaixo, a distribuição da frequência de índices e os bairros em situação mais crítica.")
    pdf.multi_cell(0, 7, texto_intro)
    
    # Espaçamento dinâmico para a primeira imagem
    pdf.ln(5)
    # Ao não passar o 'y', ele usa a posição atual do cursor
    pdf.image('panorama_geral.png', x=15, w=180) 
    
    # Pulamos um espaço proporcional ao tamanho da imagem para não sobrepor o próximo título
    pdf.ln(100) 
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '2. Ranking de Bairros Críticos', 0, 1)
    pdf.ln(2)
    pdf.image('top_criticos.png', x=15, w=180)

    # --- PÁGINA 2 EM DIANTE: TABELA ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '3. Tabela Completa de Dados por Bairro', 0, 1)
    pdf.ln(5)

    # Cabeçalho da Tabela - Ajustei larguras para somar 185 (segurança de margem)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(200, 200, 200)
    larguras = [60, 25, 25, 25, 25, 25] 
    colunas = ["Bairro", "Índice", "Famílias", "Pessoas", "Gest.", "PCDs"]
    
    for i in range(len(colunas)):
        pdf.cell(larguras[i], 10, colunas[i], 1, 0, 'C', True)
    pdf.ln()

    # Linhas da Tabela
    pdf.set_font('Arial', '', 8)
    for index, row in df.iterrows():
        fill = (index % 2 == 0)
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)

        # Usamos check para ver se precisamos repetir o cabeçalho caso mude de página
        if pdf.get_y() > 270: 
            pdf.add_page()
            pdf.set_font('Arial', 'B', 9)
            for i in range(len(colunas)):
                pdf.cell(larguras[i], 10, colunas[i], 1, 0, 'C', True)
            pdf.ln()
            pdf.set_font('Arial', '', 8)

        pdf.cell(larguras[0], 8, str(row['Bairro'])[:30], 1, 0, 'L', True)
        pdf.cell(larguras[1], 8, f"{row['Vulnerabilidade Bairro']:.2f}", 1, 0, 'C', True)
        pdf.cell(larguras[2], 8, str(int(row['Qtd Famílias'])), 1, 0, 'C', True)
        pdf.cell(larguras[3], 8, str(int(row['Qtd Total Pessoas'])), 1, 0, 'C', True)
        pdf.cell(larguras[4], 8, str(int(row['Qtd Gestantes'])), 1, 0, 'C', True)
        pdf.cell(larguras[5], 8, str(int(row['Qtd PCDs'])), 1, 0, 'C', True)
        pdf.ln()

    pdf.output('Relatorio_Socioeconomico_Slz.pdf')

def executar_geracao_relatorio():
    conn = conexao_bd()
    query = """ 
        SELECT 
            b.nome_bairro AS "Bairro",
            b.nivel_vulnerabilidade AS "Vulnerabilidade Bairro",
            COUNT(DISTINCT f.uuid_familia) AS "Qtd Famílias",
            COUNT(p.uuid_pessoa) AS "Qtd Total Pessoas",
            SUM(CASE WHEN p.gestante = 1 THEN 1 ELSE 0 END) AS "Qtd Gestantes",
            SUM(CASE WHEN p.pcd = 1 THEN 1 ELSE 0 END) AS "Qtd PCDs"
        FROM Bairros b
        LEFT JOIN Familias f ON b.uuid_bairro = f.uuid_bairro
        LEFT JOIN Pessoas p ON f.uuid_familia = p.uuid_familia
        GROUP BY b.uuid_bairro, b.nome_bairro
        ORDER BY b.nivel_vulnerabilidade DESC;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    df = df.fillna(0)

    print("[*] Gerando elementos visuais...")
    gerar_elementos_visuais(df)
    
    print("[*] Criando arquivo PDF...")
    criar_pdf_completo(df)
    print("[+] Relatório gerado com sucesso: Relatorio_Socioeconomico_Slz.pdf")

if __name__ == "__main__":
    executar_geracao_relatorio()