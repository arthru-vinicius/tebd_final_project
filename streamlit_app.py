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
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
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
    st.markdown('<h1 class="main-header">Dashboard - Análise de Voos 2015</h1>',
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
    st.sidebar.header("Informações do Projeto")
    st.sidebar.markdown("""
    **Fonte dos Dados:**
    - U.S. Department of Transportation
    - Bureau of Transportation Statistics
    - Ano: 2015

    **Volume Analisado:**
    - 5.8+ milhões de voos
    - 14 companhias aéreas
    - 7,465 rotas diferentes
    - 1.8+ milhões de problemas catalogados
    """)

    # Métricas principais
    st.header("Métricas Principais")
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
    tab1, tab2, tab3 = st.tabs(["Relatórios Tabulares", "Análises Gráficas", "Metodologia"])

    with tab1:
        st.header("Relatórios Tabulares")

        # Sub-tabs para relatórios
        rel_tab1, rel_tab2, rel_tab3, rel_tab4 = st.tabs([
            "Ranking Airlines", "Rotas Críticas", "Sazonalidade", "Causas Problemas"
        ])

        with rel_tab1:
            st.subheader("Ranking de Performance por Companhia Aérea")

            st.markdown("""
            <div class="insight-box">
            <h4>Insights Principais:</h4>
            <ul>
                <li><strong>Alaska Airlines (AS)</strong> lidera com score de 98.2</li>
                <li><strong>Spirit Airlines (NK)</strong> apresenta maior desafio (score 48.7)</li>
                <li>Diferença de <strong>49.5 pontos</strong> entre melhor e pior performance</li>
                <li>Score médio do setor: <strong>72.7 pontos</strong></li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(data['relatorio_01'], use_container_width=True, height=400)

            with st.expander("Metodologia do Ranking"):
                st.markdown("""
                **Score de Performance = Atraso Médio + (Taxa Cancelamento × 10) + (100 - Taxa Pontualidade)**

                - **Voos Pontuais**: Atraso ≤ 15 minutos
                - **Ranking**: Ordenação crescente por Performance Score (menor = melhor)
                - **Peso Cancelamentos**: 10x maior que atrasos (impacto na experiência)
                """)

        with rel_tab2:
            st.subheader("Análise de Rotas Críticas (Top 20 Piores)")

            st.markdown("""
            <div class="insight-box">
            <h4>Insights Principais:</h4>
            <ul>
                <li><strong>ASE → DFW</strong> (Aspen-Dallas): Rota mais crítica (score 282.06)</li>
                <li><strong>Rotas com aeroportos pequenos</strong> apresentam maiores desafios</li>
                <li><strong>Condições geográficas</strong> impactam significativamente a performance</li>
                <li>Concentração de problemas em <strong>hubs específicos</strong></li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(data['relatorio_02'], use_container_width=True, height=400)

            with st.expander("Metodologia das Rotas Críticas"):
                st.markdown("""
                **Score de Criticidade = Atraso Médio + (Taxa Cancelamento × 15)**

                - **Critério de Volume**: Mínimo 100 voos anuais por rota
                - **Peso Cancelamentos**: 15x maior que atrasos
                - **Análise Geográfica**: Origem e destino considerados
                """)

        with rel_tab3:
            st.subheader("Sazonalidade Detalhada - Performance Mensal")

            st.markdown("""
            <div class="insight-box">
            <h4>Insights Sazonais:</h4>
            <ul>
                <li><strong>Fevereiro</strong>: Mês mais crítico (score 82.1)</li>
                <li><strong>Abril</strong>: Melhor performance (score 29.87)</li>
                <li><strong>Verão</strong>: Maior volume, performance moderada</li>
                <li><strong>Inverno</strong>: Menor volume, maiores desafios climáticos</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(data['relatorio_03'], use_container_width=True, height=400)

            with st.expander("Metodologia da Sazonalidade"):
                st.markdown("""
                **Score de Criticidade = Atraso Médio + (Taxa Cancelamento × 10) + (100 - Taxa Pontualidade)**

                - **Análise Temporal**: Agregação mensal de métricas
                - **Causas Identificadas**: Sistema Aéreo, Segurança, Companhia, Aeronave, Clima
                """)

        with rel_tab4:
            st.subheader("Análise Detalhada de Causas de Cancelamento e Atraso")

            st.markdown("""
            <div class="insight-box">
            <h4>Insights das Causas:</h4>
            <ul>
                <li><strong>Aeronave Atrasada</strong>: Principal causa (30.1% dos casos)</li>
                <li><strong>Causas Controláveis</strong>: 60.9% dos problemas</li>
                <li><strong>Impacto Médio</strong>: 38.4 minutos por atraso</li>
                <li><strong>Oportunidade</strong>: Foco em causas controláveis para melhoria</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(data['relatorio_04'], use_container_width=True, height=400)

            with st.expander("Metodologia das Causas"):
                st.markdown("""
                **Severidade = Cancelamentos × 100 + Atrasos × Impacto Médio**

                - **Cancelamentos**: Impacto total na experiência
                - **Atrasos**: Impacto proporcional à duração
                - **Categorias**: DOT, Sistema Aéreo, Segurança, Companhia, Aeronave, Clima
                """)

    with tab2:
        st.header("Análises Gráficas Interativas")

        # Gráfico 1: Tendência Temporal
        st.subheader("1. Tendência Temporal de Atrasos ao Longo do Ano")

        col1, col2 = st.columns([3, 1])
        with col1:
            fig1 = create_temporal_trend_chart(data)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.markdown("""
            **Padrões Identificados:**

            • **Junho**: Pico de atrasos (9.4 min)
            • **Outubro**: Melhor mês (-0.8 min)
            • **Verão**: Alto volume + atrasos
            • **Inverno**: Baixo volume + variabilidade

            **Correlações:**
            • Volume ↑ → Atrasos ↑
            • Feriados → Impacto significativo
            """)

        st.markdown("---")

        # Gráfico 2: Performance Companhias
        st.subheader("2. Performance por Companhia Aérea")

        col1, col2 = st.columns([3, 1])
        with col1:
            fig2 = create_airline_performance_chart(data)
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            st.markdown("""
            **Categorias de Performance:**

            **Excelente** (≥80): AS, DL, HA
            **Boa** (70-79): UA, US, VX, AA
            **Regular** (60-69): WN, OO, EV
            **Ruim** (<60): F9, NK

            **Insights:**
            • Top 3: Operações focadas
            • Bottom 3: Desafios estruturais
            """)

        st.markdown("---")

        # Gráfico 3: Mapa de Calor
        st.subheader("3. Mapa de Calor - Atrasos por Dia vs Hora")

        col1, col2 = st.columns([3, 1])
        with col1:
            fig3 = create_heatmap_chart(data)
            st.plotly_chart(fig3, use_container_width=True)

        with col2:
            st.markdown("""
            **Padrões Temporais:**

            • **06:00-12:00**: Melhor período
            • **18:00-23:00**: Pior período
            • **Segunda-feira**: Dia mais crítico
            • **Fim de semana**: Melhor performance

            **Aplicações:**
            • Otimização de slots
            • Pricing dinâmico
            • Alocação de recursos
            """)

        st.markdown("---")

        # Gráfico 4: Distribuição de Causas
        st.subheader("4. Distribuição de Causas de Cancelamento e Atraso")

        col1, col2 = st.columns([3, 1])
        with col1:
            fig4 = create_causes_pie_chart(data)
            st.plotly_chart(fig4, use_container_width=True)

        with col2:
            st.markdown("""
            **Priorização de Ações:**

            1. **Aeronave Atrasada** (30.1%)
               → Gestão de frota

            2. **Problemas Companhia** (30.8%)
               → Processos internos

            3. **Sistema Aéreo** (30.5%)
               → Coordenação externa

            **ROI Potencial:**
            • 60.9% causas controláveis
            • Foco em top 3 = 91.4% impacto
            """)

    with tab3:
        st.header("Metodologia e Documentação Técnica")

        st.markdown("""
        ## Arquitetura do Data Warehouse

        ### Modelagem Dimensional (Esquema Estrela)
        - **Tabela Fato**: `fact_flights` (5.8M+ registros)
        - **Dimensões**: `dim_airline`, `dim_airport`, `dim_date`, `dim_flight_status`, `dim_cancellation_reason`

        ### Processo ETL
        1. **Extração**: Dados brutos do DOT (CSV)
        2. **Transformação**: Limpeza, padronização, cálculos derivados
        3. **Carga**: Estrutura dimensional otimizada

        ## Métricas e Cálculos

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

        ## Aplicações Práticas

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
        **Nota Técnica**: Este dashboard foi desenvolvido como parte do projeto de 
        Tópicos Especiais em Banco de Dados, demonstrando a aplicação prática de 
        conceitos de Data Warehouse, modelagem dimensional e análise de dados.
        """)


if __name__ == "__main__":
    main()