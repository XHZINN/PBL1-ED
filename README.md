# 📊 Monitoramento de Áreas de Risco – São Luís/MA

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B.svg)](https://streamlit.io)
[![Pandas](https://img.shields.io/badge/Pandas-150458.svg)](https://pandas.pydata.org)
![Status](https://img.shields.io/badge/Status-Conclu%C3%ADdo-green)

Uma plataforma interativa de inteligência de dados desenvolvida para mapear, analisar e monitorar indicadores socioeconômicos e níveis de vulnerabilidade de famílias residentes em áreas de risco na cidade de São Luís/MA.

> ⚠️ **Nota:** Os dados utilizados neste projeto são simulações baseadas em cenários reais para fins estritamente acadêmicos (PBL).

---

## 🚀 Sobre o Projeto

O sistema consolida dados geográficos e socioeconômicos para apoiar a tomada de decisões e ações de assistência social ou Defesa Civil. Ele transforma planilhas e bancos de dados complexos em um painel visual altamente intuitivo.

### 🌟 Principais Funcionalidades

* **Mapeamento Térmico Dinâmico:** Visualização interativa das zonas críticas de São Luís através de um mapa de calor (Folium) integrado ao modo escuro.
* **Filtros Avançados:** Segmentação de dados por intensidade de risco, bairros, faixas de renda familiar e tipos de moradia em tempo real.
* **Painel de Métricas Gerais:** Exibição clara de indicadores essenciais como renda média, vulnerabilidade média, total de pessoas afetadas e cobertura de auxílios sociais.
* **Geração de Relatórios:** Sistema automatizado para gerar relatórios socioeconômicos consolidados em formato PDF direto pela plataforma.
* **Análise Estatística:** Gráficos interativos (Barras e Rosca) via Plotly para compreender a distribuição relativa do risco por região.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem Principal:** Python 3.13
* **Interface Web:** Streamlit
* **Análise de Dados:** Pandas & Plotly Express
* **Geolocalização & Mapas:** Folium & Streamlit-Folium
* **Estilização de Tabelas:** Styler (Pandas) com degradê dinâmico `YlOrRd`

---

## 📁 Estrutura do Projeto

```text
├── monitoramento.py          # Arquivo principal (Dashboard/Mapa)
├── pages/
│   └── visualizar_familias.py # Aba de listagem detalhada e filtros de famílias
├── modulos/
│   ├── database.py           # Conexão, criação de tabelas e queries do sistema
│   └── relatorio.py          # Lógica de geração do PDF
├── requirements.txt          # Dependências do projeto para deploy
