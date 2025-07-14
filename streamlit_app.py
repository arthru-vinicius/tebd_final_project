import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from PIL import Image

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Análise de Voos 2015",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhorar aparência
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .insight-box {
        background-color: #333333;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        color: #ffffff;
    }
    .insight-item {
        margin: 0.5rem 0;
        padding: 0.3rem 0;
        border-left: 3px solid #1f77b4;
        padding-left: 0.8rem;
    }
    .highlight-metric {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 3px solid #1f77b4;
        margin: 0.5rem 0;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)


# Função para carregar dados com cache
@st.cache_data
def load_data():
    """
    Carrega todos os dados dos relatórios e gráficos
    """
    try:
        data = {}

        # Relatórios
        data['relatorio_01'] = pd.read_csv('data/relatorio_01_ranking_performance_airlines.csv')
        data['relatorio_02'] = pd.read_csv('data/relatorio_02_rotas_criticas.csv')
        data['relatorio_03'] = pd.read_csv('data/relatorio_03_sazonalidade_mensal.csv')
        data['relatorio_04'] = pd.read_csv('data/relatorio_04_causas_cancelamento_atraso.csv')

        # Dados para gráficos
        data['grafico_01'] = pd.read_csv('data/grafico_01_dados.csv')
        data['grafico_02'] = pd.read_csv('data/grafico_02_dados.csv')
        data['grafico_03_volumes'] = pd.read_csv('data/grafico_03_matriz_volumes.csv')
        data['grafico_03_atrasos'] = pd.read_csv('data/grafico_03_matriz_atrasos.csv')
        data['grafico_04_principais'] = pd.read_csv('data/grafico_04_causas_principais.csv')
        data['grafico_04_menores'] = pd.read_csv('data/grafico_04_causas_menores.csv')

        return data
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None


def create_temporal_trend_chart(data):
    """
    Cria gráfico de tendência temporal de atrasos
    """
    df = data['grafico_01']

    # Criando subplot com eixo secundário
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Linha principal - Atraso médio
    fig.add_trace(
        go.Scatter(
            x=df['month_name'],
            y=df['avg_arrival_delay'],
            mode='lines+markers',
            name='Atraso Médio (min)',
            line=dict(color='#ff6b6b', width=3),
            marker=dict(size=8)
        ),
        secondary_y=False,
    )

    # Linha secundária - Volume de voos
    fig.add_trace(
        go.Scatter(
            x=df['month_name'],
            y=df['total_flights'] / 1000,  # Em milhares
            mode='lines+markers',
            name='Volume (milhares)',
            line=dict(color='#4ecdc4', width=2),
            marker=dict(size=6)
        ),
        secondary_y=True,
    )

    # Área de pontualidade
    fig.add_trace(
        go.Scatter(
            x=df['month_name'],
            y=df['on_time_rate'],
            fill='tonexty',
            mode='none',
            name='Taxa Pontualidade (%)',
            fillcolor='rgba(78, 205, 196, 0.2)'
        ),
        secondary_y=True,
    )

    # Configurações dos eixos
    fig.update_xaxes(title_text="Mês")
    fig.update_yaxes(title_text="Atraso Médio (minutos)", secondary_y=False)
    fig.update_yaxes(title_text="Volume (milhares) / Pontualidade (%)", secondary_y=True)

    fig.update_layout(
        title="Tendência Temporal de Atrasos ao Longo de 2015",
        height=500,
        hovermode='x unified'
    )

    return fig


def create_airline_performance_chart(data):
    """
    Cria gráfico de performance por companhia aérea
    """
    df = data['grafico_02'].head(12)  # Top 12

    # Definindo cores por categoria
    color_map = {
        'Excelente': '#2ecc71',
        'Boa': '#f39c12',
        'Regular': '#e67e22',
        'Ruim': '#e74c3c'
    }

    colors = [color_map.get(cat, '#95a5a6') for cat in df['performance_category']]

    fig = go.Figure(data=[
        go.Bar(
            y=df['airline_name'],
            x=df['performance_score'],
            orientation='h',
            marker_color=colors,
            text=df['performance_score'].round(1),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>' +
                          'Score: %{x:.1f}<br>' +
                          'Pontualidade: %{customdata:.1f}%<extra></extra>',
            customdata=df['on_time_rate']
        )
    ])

    fig.update_layout(
        title="Performance por Companhia Aérea (Score de Performance)",
        xaxis_title="Score de Performance",
        yaxis_title="Companhia Aérea",
        height=600,
        showlegend=False
    )

    return fig


def create_heatmap_chart(data):
    """
    Cria mapa de calor de atrasos por dia vs hora
    """
    df_atrasos = data['grafico_03_atrasos'].set_index('day_name')

    # Convertendo colunas para numérico
    for col in df_atrasos.columns:
        df_atrasos[col] = pd.to_numeric(df_atrasos[col], errors='coerce')

    fig = go.Figure(data=go.Heatmap(
        z=df_atrasos.values,
        x=[f"{i:02d}:00" for i in range(24)],
        y=df_atrasos.index,
        colorscale='RdYlBu_r',
        zmid=0,
        colorbar=dict(title="Atraso Médio (min)"),
        hovertemplate='<b>%{y}</b><br>' +
                      'Hora: %{x}<br>' +
                      'Atraso: %{z:.1f} min<extra></extra>'
    ))

    fig.update_layout(
        title="Mapa de Calor: Atrasos por Dia da Semana vs Hora do Dia",
        xaxis_title="Hora do Dia",
        yaxis_title="Dia da Semana",
        height=500
    )

    return fig


def create_causes_pie_chart(data):
    """
    Cria gráfico de pizza das causas de problemas
    """
    df = data['grafico_04_principais']

    # Cores diferenciadas por tipo
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57']

    fig = go.Figure(data=[go.Pie(
        labels=df['cause_name'],
        values=df['percentage'],
        hole=0.3,
        marker_colors=colors,
        textinfo='label+percent',
        textposition='outside',
        hovertemplate='<b>%{label}</b><br>' +
                      'Ocorrências: %{customdata:,}<br>' +
                      'Percentual: %{percent}<extra></extra>',
        customdata=df['total_occurrences']
    )])

    fig.update_layout(
        title="Distribuição de Causas de Cancelamento e Atraso",
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5)
    )

    return fig


# INTERFACE PRINCIPAL
def main():
    # Header principal
    st.markdown('<h1 class="main-header">✈️ Dashboard - Análise de Voos 2015</h1>',
                unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h3>Data Warehouse - Tópicos Especiais em Banco de Dados</h3>
        <p><em>Análise completa de performance do setor aéreo americano em 2015</em></p>
    </div>
    """, unsafe_allow_html=True)

    # Carregamento dos dados
    with st.spinner('Carregando dados do Data Warehouse...'):
        data = load_data()

    if data is None:
        st.error("Falha ao carregar os dados. Verifique os arquivos na pasta 'data/'.")
        return

    # Sidebar com informações do projeto
    st.sidebar.header("📋 Informações do Projeto")

    st.sidebar.markdown("""
    **Fonte dos Dados:**
    - U.S. Department of Transportation
    - Bureau of Transportation Statistics
    - Ano: 2015
    - **[🔗 Link de Acesso aos Dados](https://www.kaggle.com/datasets/usdot/flight-delays?ref=hackernoon.com)**

    **Volume Analisado:**
    - 5.8+ milhões de voos
    - 14 companhias aéreas
    - 7,465 rotas diferentes
    - 1.8+ milhões de problemas catalogados

    **Integrantes da Equipe:**
    - Arthur Rodrigues
    - Athos Lima
    - Matheus Santos
    - Rafael Luna

    **Docente:**
    - Flávio Rosendo da Silva Oliveira
    """)

    # Link de acesso ao projeto
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**[🔗 Link de Acesso ao projeto no Colab](https://colab.research.google.com/drive/1K1oAjrbWChErx5YTenv3Lr5tJvm7gHnn?usp=sharing)**",
        unsafe_allow_html=True
    )

    # Métricas principais
    st.header("📊 Métricas Principais")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Voos", "5.8M+", "Analisados")
    with col2:
        st.metric("Companhias", "14", "Avaliadas")
    with col3:
        st.metric("Pontualidade Média", "79.0%", "≤ 15min atraso")
    with col4:
        st.metric("Atraso Médio", "4.4 min", "Chegada")

    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["📋 Relatórios Tabulares", "📈 Análises Gráficas", "🔍 Metodologia"])

    with tab1:
        st.header("📋 Relatórios Tabulares")

        # Sub-tabs para relatórios
        rel_tab1, rel_tab2, rel_tab3, rel_tab4 = st.tabs([
            "🏆 Ranking Airlines", "🛣️ Rotas Críticas", "📅 Sazonalidade", "⚠️ Causas Problemas"
        ])

        with rel_tab1:
            st.subheader("🏆 Ranking de Performance por Companhia Aérea")

            st.markdown("""
            <div class="insight-box">
            <h4>📈 Insights Principais:</h4>
            <ul>
                <li><strong>Alaska Airlines (AS)</strong> lidera com score de 98.2</li>
                <li><strong>Spirit Airlines (NK)</strong> apresenta maior desafio (score 48.7)</li>
                <li>Diferença de <strong>49.5 pontos</strong> entre melhor e pior performance</li>
                <li>Score médio do setor: <strong>72.7 pontos</strong></li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(data['relatorio_01'], use_container_width=True, height=400)

            with st.expander("📊 Metodologia do Ranking"):
                st.markdown("""
                **Metodologia de Cálculo:**

                O ranking é baseado em um Score de Performance que combina três componentes principais: atraso médio na chegada, taxa de cancelamento (com peso multiplicado por 10) e taxa de pontualidade invertida. A fórmula aplicada é: `Score = Atraso Médio + (Taxa Cancelamento × 10) + (100 - Taxa Pontualidade)`. Quanto menor o score, melhor a performance da companhia.

                **Métricas Analisadas:**

                Para cada companhia aérea são calculados: total de voos operados, taxa de pontualidade (voos com atraso igual ou inferior a 15 minutos), atraso médio na chegada em minutos, taxa de cancelamento, taxa de desvio de rota e o score consolidado de performance. Voos cancelados e desviados são excluídos do cálculo de pontualidade.

                **Critérios de Avaliação:**

                A análise considera voos pontuais aqueles com atraso máximo de 15 minutos na chegada, seguindo padrões internacionais da aviação civil. O peso maior atribuído aos cancelamentos reflete o impacto significativo desta ocorrência na experiência do passageiro. O processamento é otimizado através de chunks para garantir eficiência computacional com grandes volumes de dados.
                """)

        with rel_tab2:
            st.subheader("🛣️ Análise de Rotas Críticas (Top 20 Piores)")

            st.markdown("""
            <div class="insight-box">
            <h4>🎯 Insights Principais:</h4>
            <ul>
                <li><strong>ASE → DFW</strong> (Aspen-Dallas): Rota mais crítica (score 282.06)</li>
                <li><strong>Rotas com aeroportos pequenos</strong> apresentam maiores desafios</li>
                <li><strong>Condições geográficas</strong> impactam significativamente a performance</li>
                <li>Concentração de problemas em <strong>hubs específicos</strong></li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(data['relatorio_02'], use_container_width=True, height=400)

            with st.expander("📊 Metodologia das Rotas Críticas"):
                st.markdown("""
                **Metodologia de Análise:**

                A análise considera todas as rotas com volume mínimo de 100 voos anuais para garantir significância estatística. Para cada rota origem-destino são calculados indicadores de performance incluindo atraso médio na chegada, taxa de cancelamento, volume total de operações e distância percorrida. O ranking é estabelecido através de um score composto que pondera negativamente atrasos e cancelamentos.

                **Critérios de Seleção:**

                As rotas são classificadas como críticas baseando-se em múltiplos fatores de impacto operacional. O score de criticidade combina atraso médio na chegada com taxa de cancelamento multiplicada por fator de peso 15, refletindo o impacto desproporcional dos cancelamentos na experiência do passageiro. Rotas com menos de 100 voos anuais são excluídas para evitar distorções estatísticas.

                **Enriquecimento de Dados:**

                Para cada rota crítica identificada são coletadas informações complementares incluindo cidades de origem e destino, estados envolvidos, regiões geográficas e lista das companhias aéreas que operam a conexão. Estes dados permitem análise geográfica e identificação de padrões regionais de problemas operacionais.

                **Métricas Calculadas:**

                O relatório apresenta para cada rota crítica o volume total de voos, atraso médio na chegada em minutos, taxa de cancelamento percentual, distância da rota em milhas e relação completa das companhias que operam a conexão. Adicionalmente são fornecidas estatísticas comparativas com médias nacionais para contextualização dos problemas identificados.
                """)

        with rel_tab3:
            st.subheader("📅 Sazonalidade Detalhada - Performance Mensal")

            st.markdown("""
            <div class="insight-box">
            <h4>🌡️ Insights Sazonais:</h4>
            <ul>
                <li><strong>Fevereiro</strong>: Mês mais crítico (score 82.1)</li>
                <li><strong>Abril</strong>: Melhor performance (score 29.87)</li>
                <li><strong>Verão</strong>: Maior volume, performance moderada</li>
                <li><strong>Inverno</strong>: Menor volume, maiores desafios climáticos</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(data['relatorio_03'], use_container_width=True, height=400)

            with st.expander("📊 Metodologia da Sazonalidade"):
                st.markdown("""
                **Metodologia de Análise Temporal:**

                A análise considera todos os voos realizados em 2015 agrupados por mês, calculando métricas consolidadas de performance para cada período. São analisados indicadores de volume operacional, pontualidade, atrasos médios, cancelamentos e principais causas de problemas operacionais. A metodologia permite identificação de meses críticos e períodos de melhor performance.

                **Métricas de Sazonalidade:**

                Para cada mês são calculados o volume total de voos operados, quantidade de voos pontuais dentro do critério de 15 minutos, total de voos atrasados, voos cancelados e atraso médio na chegada. Adicionalmente são identificadas as principais causas de atraso por período, permitindo análise detalhada dos fatores sazonais que impactam a operação.

                **Análise de Causas Temporais:**

                O relatório detalha a distribuição mensal dos diferentes tipos de atraso incluindo problemas de sistema aéreo, questões meteorológicas, problemas das companhias aéreas, atrasos de aeronaves e questões de segurança. Esta segmentação permite identificar quais fatores são mais prevalentes em determinados períodos do ano.

                **Identificação de Padrões Cíclicos:**

                A análise temporal revela padrões recorrentes relacionados a feriados, condições climáticas sazonais, períodos de alta demanda turística e variações operacionais típicas da aviação comercial. Estes insights são fundamentais para planejamento de capacidade e estratégias de mitigação de problemas sazonais.
                """)

        with rel_tab4:
            st.subheader("⚠️ Análise Detalhada de Causas de Cancelamento e Atraso")

            st.markdown("""
            <div class="insight-box">
            <h4>🔍 Insights das Causas:</h4>
            <ul>
                <li><strong>Aeronave Atrasada</strong>: Principal causa (30.1% dos casos)</li>
                <li><strong>Causas Controláveis</strong>: 60.9% dos problemas</li>
                <li><strong>Impacto Médio</strong>: 38.4 minutos por atraso</li>
                <li><strong>Oportunidade</strong>: Foco em causas controláveis para melhoria</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(data['relatorio_04'], use_container_width=True, height=400)

            with st.expander("📊 Metodologia das Causas"):
                st.markdown("""
                **Metodologia de Categorização:**

                A análise segmenta os problemas operacionais em duas categorias principais: cancelamentos e atrasos. Para cancelamentos são analisadas as causas codificadas pelo sistema DOT incluindo problemas de companhia aérea, condições meteorológicas, sistema aéreo nacional e questões de segurança. Para atrasos são quantificados os diferentes tipos de delay com seus respectivos impactos temporais.

                **Quantificação de Impactos:**

                Para cada tipo de problema são calculadas métricas de frequência absoluta, percentual do total de ocorrências, impacto médio em minutos de atraso e identificação dos meses com maior incidência. Esta abordagem permite priorização de ações corretivas baseada em impacto real na operação e experiência do passageiro.

                **Análise Temporal de Causas:**

                O relatório identifica padrões sazonais nas diferentes causas de problemas, revelando quais fatores são mais prevalentes em determinados períodos do ano. Esta análise temporal é fundamental para planejamento preventivo e alocação de recursos para mitigação de problemas recorrentes.

                **Segmentação por Severidade:**

                Os problemas são categorizados por níveis de severidade baseados no impacto operacional, permitindo foco em causas que geram maior disrução. Cancelamentos recebem peso maior devido ao impacto total na experiência do passageiro, enquanto atrasos são ponderados pela duração média do impacto.
                """)

    with tab2:
        st.header("📈 Análises Gráficas Interativas")

        # Gráfico 1: Tendência Temporal
        st.subheader("📊 1. Tendência Temporal de Atrasos ao Longo do Ano")

        col1, col2 = st.columns([3, 1])
        with col1:
            fig1 = create_temporal_trend_chart(data)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.markdown("""
            ### 🔍 **Insights Principais:**
            """)

            st.markdown("""
            <div class="insight-item">
            <strong>📈 Padrão Sazonal Crítico:</strong><br>
            Janeiro, Fevereiro, Junho, Julho e Dezembro apresentam atrasos significativamente maiores
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="highlight-metric">
            <strong>🎯 Insight Chave:</strong><br>
            Volume varia pouco (~10%), mas atrasos variam drasticamente (até 1000%)
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            **🌡️ Causas Identificadas:**
            - **Inverno** (Jan/Fev/Dez): Condições climáticas adversas
            - **Verão** (Jun/Jul): Pico de demanda turística
            - **Abril/Maio**: Condições ideais (clima + demanda)

            **💡 Recomendação:**
            Ajuste de capacidade e recursos nos meses críticos
            """)

        st.markdown("---")

        # Gráfico 2: Performance Companhias
        st.subheader("🏆 2. Performance por Companhia Aérea")

        col1, col2 = st.columns([3, 1])
        with col1:
            fig2 = create_airline_performance_chart(data)
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            st.markdown("""
            ### 🎯 **Categorização:**
            """)

            st.markdown("""
            <div class="insight-item">
            🟢 <strong>Excelente (≥80):</strong><br>
            AS, DL, HA - Operações focadas e eficientes
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="insight-item">
            🟠 <strong>Boa (70-79):</strong><br>
            UA, US, VX, AA - Performance sólida
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="insight-item">
            🔴 <strong>Desafios (<60):</strong><br>
            F9, NK - Necessitam melhorias estruturais
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            **📊 Diferencial Competitivo:**
            - **49.5 pontos** entre melhor e pior
            - **Alaska Airlines**: Benchmark do setor
            - **Oportunidade**: Grandes variações indicam potencial de melhoria
            """)

        st.markdown("---")

        # Gráfico 3: Mapa de Calor
        st.subheader("🌡️ 3. Mapa de Calor - Atrasos por Dia vs Hora")

        col1, col2 = st.columns([3, 1])
        with col1:
            fig3 = create_heatmap_chart(data)
            st.plotly_chart(fig3, use_container_width=True)

        with col2:
            st.markdown("""
            ### ⏰ **Padrões Temporais:**
            """)

            st.markdown("""
            <div class="insight-item">
            <strong>🌅 Manhã (06-12h):</strong><br>
            Melhor período - operações "limpas"
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="insight-item">
            <strong>🌆 Tarde/Noite (18-23h):</strong><br>
            Período crítico - efeito cascata
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="highlight-metric">
            <strong>📈 Efeito Cascata:</strong><br>
            Atrasos se acumulam ao longo do dia
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            **🎯 Aplicações Práticas:**
            - **Pricing dinâmico**: Horários premium vs econômicos
            - **Alocação de recursos**: Reforço em períodos críticos
            - **Planejamento**: Slots estratégicos para voos importantes
            """)

        st.markdown("---")

        # Gráfico 4: Distribuição de Causas
        st.subheader("🥧 4. Distribuição de Causas de Cancelamento e Atraso")

        col1, col2 = st.columns([3, 1])
        with col1:
            fig4 = create_causes_pie_chart(data)
            st.plotly_chart(fig4, use_container_width=True)

        with col2:
            st.markdown("""
            ### 🎯 **Priorização de Ações:**
            """)

            st.markdown("""
            <div class="insight-item">
            <strong>1️⃣ Aeronave Atrasada (30.1%):</strong><br>
            Gestão de frota e manutenção preventiva
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="insight-item">
            <strong>2️⃣ Problemas Companhia (30.8%):</strong><br>
            Otimização de processos internos
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="highlight-metric">
            <strong>💰 ROI Potencial:</strong><br>
            60.9% das causas são controláveis
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            **🚀 Estratégia Recomendada:**
            - **Foco no Top 3**: 91.4% do impacto total
            - **Quick Wins**: Causas controláveis primeiro
            - **Investimento**: Tecnologia e processos
            """)

    with tab3:
        st.header("🔍 Metodologia e Documentação Técnica")

        st.markdown("""
        ## 🏗️ Arquitetura do Data Warehouse

        ### Modelagem Dimensional (Esquema Estrela)
        - **Tabela Fato**: `fact_flights` (5.8M+ registros)
        - **Dimensões**: `dim_airline`, `dim_airport`, `dim_date`, `dim_flight_status`, `dim_cancellation_reason`

        ### Processo ETL
        1. **Extração**: Dados brutos do DOT (CSV)
        2. **Transformação**: Limpeza, padronização, cálculos derivados
        3. **Carga**: Estrutura dimensional otimizada

        ## 📊 Métricas e Cálculos

        ### Score de Performance (Airlines)
        ```
        Score = Atraso_Médio + (Taxa_Cancelamento × 10) + (100 - Taxa_Pontualidade)
        ```

        ### Score de Criticidade (Rotas)
        ```
        Score = Atraso_Médio + (Taxa_Cancelamento × 15)
        ```

        ### Definições Operacionais
        - **Voo Pontual**: Atraso ≤ 15 minutos
        - **Atraso Significativo**: > 15 minutos
        - **Volume Mínimo**: 100 voos/ano para análise de rotas

        ## 🎯 Aplicações Práticas

        ### Para Companhias Aéreas
        - Benchmarking de performance
        - Identificação de oportunidades de melhoria
        - Planejamento de investimentos

        ### Para Aeroportos
        - Otimização de slots
        - Gestão de recursos por horário
        - Planejamento de capacidade

        ### Para Passageiros
        - Escolha de companhias
        - Planejamento de viagens
        - Expectativas realistas
        """)

        st.info("""
        💡 **Nota Técnica**: Este dashboard foi desenvolvido como parte do projeto de 
        Tópicos Especiais em Banco de Dados, demonstrando a aplicação prática de 
        conceitos de Data Warehouse, modelagem dimensional e análise de dados.
        """)


if __name__ == "__main__":
    main()