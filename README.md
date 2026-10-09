# Monitoramento de Áreas de Risco — São Luís/MA

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B.svg)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/SQLite-003B57.svg)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Plataforma de apoio à decisão para assistência social e Defesa Civil, que cadastra famílias
residentes em áreas de risco de São Luís/MA, calcula um índice de vulnerabilidade para cada uma
delas e agrega esse resultado por bairro, exibindo-o em um mapa de calor e em painéis analíticos.

**Aplicação no ar:** https://monitoramentopbl1.streamlit.app

> Os dados deste repositório são simulados. O projeto foi desenvolvido como trabalho acadêmico
> (PBL) e não utiliza informações reais de nenhuma família.

---

## O que o sistema faz

O ponto de partida é o cadastro de uma família: composição do núcleo, renda, tipo e custo de
moradia, bairro e recebimento de auxílio social. A partir daí o sistema:

1. calcula um índice de vulnerabilidade de 0 a 10 para a família;
2. recalcula a média do bairro ao qual ela pertence;
3. repinta o mapa de calor e os gráficos com o novo valor.

Visitas técnicas posteriores registram a situação da família ao longo do tempo, o que permite
acompanhar a evolução mensal da vulnerabilidade por bairro.

### Como o índice é calculado

A regra está em [`modulos/calculos.py`](modulos/calculos.py) e combina dois componentes.

**Renda per capita** (renda familiar dividida pelo número de membros), em faixas baseadas nas
linhas de pobreza e no salário mínimo:

| Renda per capita | Peso |
| --- | --- |
| até R$ 218 (extrema pobreza) | 4 |
| até R$ 625 (pobreza) | 3 |
| até R$ 1.212 (baixa renda) | 2 |
| até R$ 3.030 (média renda) | 1 |
| acima disso | 0 |

**Perfil dos membros**, somado por pessoa e depois promediado: crianças com menos de 5 anos e
idosos a partir de 60 valem 3 pontos; adolescentes até 17 valem 2; adultos valem 1. Gestação e
deficiência somam 2 pontos cada.

O índice final pondera os dois componentes e satura em 10:

```
indice = min(10, (peso_renda * 1.5 + media_pesos_membros * 1.2) * 0.7)
```

A vulnerabilidade de um bairro é a média simples das famílias cadastradas nele.

---

## Páginas

| Página | Arquivo | Descrição |
| --- | --- | --- |
| Monitoramento | [`monitoramento.py`](monitoramento.py) | Painel inicial. Mapa de calor de São Luís com marcador clicável por bairro, filtro de intensidade mínima, métricas gerais, tabela ordenada por risco e gráficos de barras e rosca. Gera o relatório em PDF. |
| Cadastro | [`pages/cadastro.py`](pages/cadastro.py) | Formulário de cadastro de família e de seus membros, com validação de CPF, nome, data e telefone. Cria o bairro automaticamente via geocodificação quando ele ainda não existe. |
| Visitas | [`pages/visitas.py`](pages/visitas.py) | Registro de visitas técnicas. Localiza a família pelo responsável, atualiza renda e auxílio no momento da visita e grava observações. |
| Visualizar famílias | [`pages/visualizar_familias.py`](pages/visualizar_familias.py) | Lista das famílias cadastradas, com filtros, detalhamento dos membros e gráficos de distribuição. |
| Análise por bairros | [`pages/analise_bairros.py`](pages/analise_bairros.py) | Análise comparativa entre bairros, com filtros por localização, período e indicadores, e evolução temporal da vulnerabilidade. |
| Comparação | [`pages/comparação.py`](pages/comparação.py) | Comparação de desempenho entre Merge Sort, Quick Sort e Bubble Sort ordenando os nomes dos responsáveis, com medição de tempo. |

A página de comparação é o componente da disciplina de Estruturas de Dados: os três algoritmos
são implementados à mão, sem usar `sorted`, e rodam sobre a base real de responsáveis cadastrados.

---

## Tecnologias

- **Python 3.13** e **Streamlit** para a aplicação e o roteamento entre páginas
- **SQLite** como banco de dados, em arquivo único versionado no repositório
- **Folium** e **streamlit-folium** para o mapa, que é Leaflet renderizado dentro de um iframe
- **Plotly Express** e **Altair** para os gráficos
- **Pandas** para manipulação tabular
- **Geopy** (Nominatim) para geocodificar bairros no cadastro
- **FPDF**, **Matplotlib** e **Seaborn** para o relatório em PDF

---

## Estrutura

```text
monitoramento.py              Painel inicial: mapa de calor, métricas, tabela e gráficos
Banco_dados.db                Banco SQLite com os dados simulados
requirements.txt              Dependências
.streamlit/config.toml        Tema escuro da interface

modulos/
  database.py                 Conexão, criação das tabelas, CRUD e consultas agregadas
  calculos.py                 Índice de vulnerabilidade e cálculo de idade
  validacao.py                Validação de CPF, nome, data e telefone
  relatorio.py                Geração do relatório socioeconômico em PDF

pages/
  cadastro.py                 Cadastro de famílias e membros
  visitas.py                  Registro de visitas técnicas
  visualizar_familias.py      Listagem e detalhamento das famílias
  analise_bairros.py          Análise comparativa entre bairros
  comparação.py               Comparação de algoritmos de ordenação
```

---

## Banco de dados

Cinco tabelas, criadas automaticamente na primeira execução por `criar_table()`.

| Tabela | Registros | Conteúdo |
| --- | --- | --- |
| `Bairros` | 42 | Nome, coordenadas e vulnerabilidade média |
| `Familias` | 1.202 | Núcleo familiar, renda, moradia, auxílio e última visita |
| `Pessoas` | 4.884 | Membros das famílias, com idade, gestação e deficiência |
| `Visitas` | 14.403 | Histórico de visitas técnicas |
| `Backup` | 0 | Controle de cópias de segurança |

`Familias` e `Visitas` referenciam `Bairros` e `Familias` por chave estrangeira. A vulnerabilidade
é desnormalizada em `Familias` e `Bairros` para evitar recalcular tudo a cada carregamento de
página; `sincronizar_vulnerabilidades_completo()` recalcula a árvore inteira quando necessário.

---

## Como executar

Requer Python 3.13 ou superior.

Clone o repositório e entre na pasta:

```bash
git clone https://github.com/XHZINN/PBL1-ED.git
cd PBL1-ED
```

Crie um ambiente virtual e instale as dependências.

No Windows:

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Suba a aplicação:

```bash
streamlit run monitoramento.py
```

O Streamlit abre o navegador em `http://localhost:8501`. O banco já vem populado, então o mapa
e os painéis aparecem preenchidos na primeira execução.

---

## Notas de manutenção

**Camada de base do mapa.** O Folium gera Leaflet, que por si só não contém mapa nenhum: ele
busca as imagens de fundo em um servidor de tiles. O provedor CartoDB, usado originalmente,
passou a exigir chave de API e responde com uma imagem de aviso no lugar do mapa. O projeto usa
o basemap escuro da Esri, que é aberto e dispensa cadastro. Se o mapa aparecer cinza com a frase
"API KEY REQUIRED", a causa é essa: o parâmetro `tiles` em `monitoramento.py` precisa apontar
para um provedor válido, acompanhado de `attr`.

**Geocodificação.** O cadastro de um bairro inédito consulta o Nominatim, que impõe limite de
requisições e exige conexão. Bairros já cadastrados não disparam nova consulta.

---

## Autores

Projeto desenvolvido em dupla:

- [XHZINN](https://github.com/XHZINN)
- [loky070](https://github.com/loky070)

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE).
