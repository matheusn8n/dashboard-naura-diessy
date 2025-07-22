#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Executivo - Naura vs Diessy (Versão com Filtro por Dia)
Sistema web interativo com filtro de data para análise diária
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import io

# Configuração da página
st.set_page_config(
    page_title="Dashboard Executivo - Naura vs Diessy",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f4e79;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f8ff, #e6f3ff);
        border-radius: 10px;
        border-left: 5px solid #1f4e79;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2e8b57;
        margin: 0.5rem 0;
    }
    
    .alert-success {
        background: #e6ffe6;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .alert-warning {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .comparison-winner {
        background: #e6ffe6;
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    
    .filter-info {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .day-summary {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def processar_tempo_espera(tempo_str):
    """Converte tempo para minutos"""
    if pd.isna(tempo_str) or tempo_str == '-' or tempo_str == '':
        return None
    
    try:
        tempo_str = str(tempo_str).strip()
        if ':' in tempo_str:
            partes = tempo_str.split(':')
            if len(partes) >= 2:
                horas = int(partes[0])
                minutos = int(partes[1])
                segundos = int(partes[2]) if len(partes) > 2 else 0
                return horas * 60 + minutos + segundos / 60
        return None
    except:
        return None

def classificar_faixa_tempo(minutos):
    """Classifica tempo em faixas"""
    if pd.isna(minutos):
        return "Sem dados"
    
    if minutos <= 1:
        return "Até 1 min"
    elif minutos <= 5:
        return "1-5 min"
    elif minutos <= 10:
        return "6-10 min"
    elif minutos <= 30:
        return "11-30 min"
    elif minutos <= 120:
        return "30min-2h"
    else:
        return "Mais de 2h"

def processar_dados(df):
    """Processa dados do Octadesk"""
    try:
        # Filtrar Naura e Diessy
        mask_naura = df['Responsável da conversa'].str.contains('Naura', case=False, na=False)
        mask_diessy = df['Responsável da conversa'].str.contains('Diessy', case=False, na=False)
        df_filtrado = df[mask_naura | mask_diessy].copy()
        
        if len(df_filtrado) == 0:
            return None
        
        # Processar datas
        df_filtrado['data_entrada'] = pd.to_datetime(df_filtrado['Data e hora de entrada'], format='%d/%m/%Y %H:%M', errors='coerce')
        df_filtrado['data_apenas'] = df_filtrado['data_entrada'].dt.date
        df_filtrado['hora_entrada'] = df_filtrado['data_entrada'].dt.hour
        df_filtrado['dia_semana'] = df_filtrado['data_entrada'].dt.day_name()
        
        # Limpar nome do responsável
        df_filtrado['atendente'] = df_filtrado['Responsável da conversa'].apply(
            lambda x: "Naura" if "naura" in str(x).lower() else "Diessy"
        )
        
        # Processar tempo de espera
        if 'Tempo de espera após atribuição' in df_filtrado.columns:
            df_filtrado['tempo_espera_min'] = df_filtrado['Tempo de espera após atribuição'].apply(processar_tempo_espera)
            df_filtrado['faixa_tempo'] = df_filtrado['tempo_espera_min'].apply(classificar_faixa_tempo)
        
        return df_filtrado
        
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return None

def filtrar_por_data(df, data_selecionada, tipo_filtro):
    """Filtra dados por data"""
    if tipo_filtro == "Dia específico":
        return df[df['data_apenas'] == data_selecionada]
    else:  # Todos os dados
        return df

def calcular_metricas(df, data_filtro=None, tipo_filtro="Todos os dados"):
    """Calcula métricas para o dashboard"""
    if df is None or len(df) == 0:
        return {}
    
    # Aplicar filtro se necessário
    if tipo_filtro == "Dia específico" and data_filtro:
        df_filtrado = filtrar_por_data(df, data_filtro, tipo_filtro)
        periodo_texto = f"Dia {data_filtro.strftime('%d/%m/%Y')}"
        periodo_dias = 1
    else:
        df_filtrado = df
        periodo_dias = df['data_apenas'].nunique()
        data_inicio = df['data_apenas'].min()
        data_fim = df['data_apenas'].max()
        if periodo_dias == 1:
            periodo_texto = f"Dia {data_inicio.strftime('%d/%m/%Y')}"
        else:
            periodo_texto = f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
    
    if len(df_filtrado) == 0:
        return {
            'sem_dados': True,
            'periodo_texto': periodo_texto,
            'data_filtro': data_filtro
        }
    
    # Métricas gerais
    total_clientes = len(df_filtrado)
    
    # Métricas por atendente
    naura_df = df_filtrado[df_filtrado['atendente'] == 'Naura']
    diessy_df = df_filtrado[df_filtrado['atendente'] == 'Diessy']
    
    naura_total = len(naura_df)
    diessy_total = len(diessy_df)
    
    naura_media = naura_total / periodo_dias if periodo_dias > 0 else 0
    diessy_media = diessy_total / periodo_dias if periodo_dias > 0 else 0
    
    # Tempo médio (se disponível)
    naura_tempo = 0
    diessy_tempo = 0
    
    if 'tempo_espera_min' in df_filtrado.columns:
        naura_tempos = naura_df['tempo_espera_min'].dropna()
        diessy_tempos = diessy_df['tempo_espera_min'].dropna()
        
        naura_tempo = naura_tempos.mean() if len(naura_tempos) > 0 else 0
        diessy_tempo = diessy_tempos.mean() if len(diessy_tempos) > 0 else 0
    
    # Distribuição por faixa de tempo
    naura_dist = {}
    diessy_dist = {}
    
    if 'faixa_tempo' in df_filtrado.columns:
        naura_dist = naura_df['faixa_tempo'].value_counts().to_dict()
        diessy_dist = diessy_df['faixa_tempo'].value_counts().to_dict()
    
    # Distribuição por hora (para análise do dia)
    naura_por_hora = naura_df['hora_entrada'].value_counts().sort_index().to_dict() if tipo_filtro == "Dia específico" else {}
    diessy_por_hora = diessy_df['hora_entrada'].value_counts().sort_index().to_dict() if tipo_filtro == "Dia específico" else {}
    
    return {
        'sem_dados': False,
        'geral': {
            'total_clientes': total_clientes,
            'periodo_dias': periodo_dias,
            'periodo_texto': periodo_texto,
            'media_diaria': total_clientes / periodo_dias if periodo_dias > 0 else 0
        },
        'naura': {
            'total': naura_total,
            'media_diaria': naura_media,
            'tempo_medio': naura_tempo,
            'distribuicao_tempo': naura_dist,
            'por_hora': naura_por_hora
        },
        'diessy': {
            'total': diessy_total,
            'media_diaria': diessy_media,
            'tempo_medio': diessy_tempo,
            'distribuicao_tempo': diessy_dist,
            'por_hora': diessy_por_hora
        },
        'dados_filtrados': df_filtrado,
        'tipo_filtro': tipo_filtro,
        'data_filtro': data_filtro
    }

def main():
    """Função principal do dashboard"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        📊 DASHBOARD EXECUTIVO - PERFORMANCE ATENDIMENTO
        <br><small>Análise Comparativa: Naura vs Diessy</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar para filtros
    st.sidebar.markdown("## 🔍 Filtros de Análise")
    
    # Upload de arquivo
    st.sidebar.markdown("### 📁 Upload do Arquivo")
    uploaded_file = st.sidebar.file_uploader(
        "Arquivo Excel do Octadesk",
        type=['xlsx', 'xls'],
        help="Faça upload do arquivo de conversas exportado do Octadesk"
    )
    
    if uploaded_file is None:
        st.markdown("""
        ## 📁 Upload do Arquivo do Octadesk
        
        👆 **Use a barra lateral** para fazer upload do arquivo Excel exportado do Octadesk
        
        ### 📋 Como exportar do Octadesk:
        1. Acesse o Octadesk
        2. Vá em **Relatórios**
        3. Selecione **Total de conversas**
        4. Escolha o período desejado
        5. Clique em **Exportar** → **Excel**
        6. Faça upload do arquivo na barra lateral
        """)
        return
    
    # Carregar dados
    try:
        df = pd.read_excel(uploaded_file)
        st.sidebar.success(f"✅ Arquivo carregado: {len(df)} registros")
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao carregar arquivo: {e}")
        return
    
    # Processar dados
    dados_processados = processar_dados(df)
    
    if dados_processados is None or len(dados_processados) == 0:
        st.error("❌ Nenhum dado encontrado para Naura ou Diessy")
        st.info("Verifique se o arquivo contém dados das atendentes Naura e Diessy")
        return
    
    # Filtros de data
    st.sidebar.markdown("### 📅 Filtro por Data")
    
    # Obter datas disponíveis
    datas_disponiveis = sorted(dados_processados['data_apenas'].unique())
    data_min = min(datas_disponiveis)
    data_max = max(datas_disponiveis)
    
    # Tipo de filtro
    tipo_filtro = st.sidebar.radio(
        "Tipo de análise:",
        ["Todos os dados", "Dia específico"],
        help="Escolha se quer ver todos os dados ou apenas um dia específico"
    )
    
    data_selecionada = None
    if tipo_filtro == "Dia específico":
        data_selecionada = st.sidebar.selectbox(
            "Escolha o dia:",
            datas_disponiveis,
            format_func=lambda x: x.strftime('%d/%m/%Y - %A'),
            help="Selecione o dia específico para análise"
        )
        
        # Informações do dia selecionado
        dados_dia = dados_processados[dados_processados['data_apenas'] == data_selecionada]
        st.sidebar.markdown(f"""
        <div class="filter-info">
            <strong>📅 Dia Selecionado:</strong><br>
            {data_selecionada.strftime('%d/%m/%Y - %A')}<br>
            <strong>📊 Registros:</strong> {len(dados_dia)}<br>
            <strong>👥 Naura:</strong> {len(dados_dia[dados_dia['atendente'] == 'Naura'])}<br>
            <strong>👥 Diessy:</strong> {len(dados_dia[dados_dia['atendente'] == 'Diessy'])}
        </div>
        """, unsafe_allow_html=True)
    
    # Calcular métricas com filtro
    metricas = calcular_metricas(dados_processados, data_selecionada, tipo_filtro)
    
    if metricas.get('sem_dados', False):
        st.warning(f"⚠️ Nenhum dado encontrado para {metricas['periodo_texto']}")
        return
    
    # Informações do período
    st.sidebar.markdown("### 📊 Informações do Período")
    st.sidebar.info(f"""
    **Período:** {metricas['geral']['periodo_texto']}
    **Total de registros:** {metricas['geral']['total_clientes']}
    **Naura:** {metricas['naura']['total']} clientes
    **Diessy:** {metricas['diessy']['total']} clientes
    **Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """)
    
    # === SEÇÃO 1: INDICADOR DE FILTRO ===
    if tipo_filtro == "Dia específico":
        st.markdown(f"""
        <div class="filter-info">
            <strong>🔍 FILTRO ATIVO:</strong> Exibindo dados apenas do dia {data_selecionada.strftime('%d/%m/%Y - %A')}
            <br><small>Para ver todos os dados, altere o filtro na barra lateral</small>
        </div>
        """, unsafe_allow_html=True)
    
    # === SEÇÃO 2: MÉTRICAS PRINCIPAIS ===
    st.markdown("## 📈 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total de Clientes",
            value=f"{metricas['geral']['total_clientes']:,}",
            delta=f"Período: {metricas['geral']['periodo_dias']} dia(s)"
        )
    
    with col2:
        if tipo_filtro == "Dia específico":
            st.metric(
                label="Clientes no Dia",
                value=f"{metricas['geral']['total_clientes']:,}",
                delta="dia selecionado"
            )
        else:
            st.metric(
                label="Média Diária",
                value=f"{metricas['geral']['media_diaria']:.1f}",
                delta="clientes/dia"
            )
    
    with col3:
        st.metric(
            label="Clientes Naura",
            value=f"{metricas['naura']['total']:,}",
            delta=f"{metricas['naura']['media_diaria']:.1f}/dia" if tipo_filtro != "Dia específico" else "no dia"
        )
    
    with col4:
        st.metric(
            label="Clientes Diessy", 
            value=f"{metricas['diessy']['total']:,}",
            delta=f"{metricas['diessy']['media_diaria']:.1f}/dia" if tipo_filtro != "Dia específico" else "no dia"
        )
    
    # === SEÇÃO 3: ANÁLISE ESPECÍFICA DO DIA ===
    if tipo_filtro == "Dia específico":
        st.markdown("## 🕐 Análise por Hora do Dia")
        
        # Gráfico de distribuição por hora
        horas_naura = metricas['naura']['por_hora']
        horas_diessy = metricas['diessy']['por_hora']
        
        if horas_naura or horas_diessy:
            # Preparar dados para gráfico
            todas_horas = list(range(24))
            valores_naura = [horas_naura.get(h, 0) for h in todas_horas]
            valores_diessy = [horas_diessy.get(h, 0) for h in todas_horas]
            
            fig_horas = go.Figure()
            
            fig_horas.add_trace(go.Bar(
                x=todas_horas,
                y=valores_naura,
                name='Naura',
                marker_color='#2E8B57',
                opacity=0.8
            ))
            
            fig_horas.add_trace(go.Bar(
                x=todas_horas,
                y=valores_diessy,
                name='Diessy',
                marker_color='#DC143C',
                opacity=0.8
            ))
            
            fig_horas.update_layout(
                title=f"Distribuição de Clientes por Hora - {data_selecionada.strftime('%d/%m/%Y')}",
                xaxis_title="Hora do Dia",
                yaxis_title="Número de Clientes",
                barmode='group',
                height=400
            )
            
            st.plotly_chart(fig_horas, use_container_width=True)
            
            # Insights do dia
            hora_pico_naura = max(horas_naura.items(), key=lambda x: x[1]) if horas_naura else (0, 0)
            hora_pico_diessy = max(horas_diessy.items(), key=lambda x: x[1]) if horas_diessy else (0, 0)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="day-summary">
                    <h4>📊 Naura - {data_selecionada.strftime('%d/%m/%Y')}</h4>
                    <p><strong>Total:</strong> {metricas['naura']['total']} clientes</p>
                    <p><strong>Hora de pico:</strong> {hora_pico_naura[0]:02d}:00 ({hora_pico_naura[1]} clientes)</p>
                    <p><strong>Tempo médio:</strong> {metricas['naura']['tempo_medio']:.1f} min</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="day-summary">
                    <h4>📊 Diessy - {data_selecionada.strftime('%d/%m/%Y')}</h4>
                    <p><strong>Total:</strong> {metricas['diessy']['total']} clientes</p>
                    <p><strong>Hora de pico:</strong> {hora_pico_diessy[0]:02d}:00 ({hora_pico_diessy[1]} clientes)</p>
                    <p><strong>Tempo médio:</strong> {metricas['diessy']['tempo_medio']:.1f} min</p>
                </div>
                """, unsafe_allow_html=True)
    
    # === SEÇÃO 4: COMPARATIVO EXECUTIVO ===
    st.markdown("## 🏆 Comparativo de Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        melhor_volume = "Naura" if metricas['naura']['total'] > metricas['diessy']['total'] else "Diessy"
        if melhor_volume == "Naura":
            st.markdown(f"""
            <div class="comparison-winner">
                <h3>👑 MAIOR VOLUME</h3>
                <h2>NAURA</h2>
                <p>{metricas['naura']['total']} clientes</p>
                <p>{metricas['naura']['media_diaria']:.1f} clientes/dia</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="comparison-winner">
                <h3>👑 MAIOR VOLUME</h3>
                <h2>DIESSY</h2>
                <p>{metricas['diessy']['total']} clientes</p>
                <p>{metricas['diessy']['media_diaria']:.1f} clientes/dia</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        naura_tempo = metricas['naura']['tempo_medio']
        diessy_tempo = metricas['diessy']['tempo_medio']
        
        if naura_tempo > 0 and diessy_tempo > 0:
            melhor_tempo = "Naura" if naura_tempo < diessy_tempo else "Diessy"
            if melhor_tempo == "Naura":
                st.markdown(f"""
                <div class="comparison-winner">
                    <h3>⚡ MAIS RÁPIDA</h3>
                    <h2>NAURA</h2>
                    <p>Tempo médio: {naura_tempo:.1f} min</p>
                    <p>Resposta mais ágil</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="comparison-winner">
                    <h3>⚡ MAIS RÁPIDA</h3>
                    <h2>DIESSY</h2>
                    <p>Tempo médio: {diessy_tempo:.1f} min</p>
                    <p>Resposta mais ágil</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="comparison-winner">
                <h3>⚡ TEMPO DE RESPOSTA</h3>
                <h2>DADOS INDISPONÍVEIS</h2>
                <p>Verifique coluna de tempo</p>
            </div>
            """, unsafe_allow_html=True)
    
    # === SEÇÃO 5: GRÁFICOS INTERATIVOS ===
    st.markdown("## 📊 Análise Visual")
    
    # Gráfico 1: Volume (adaptado para filtro)
    if tipo_filtro == "Todos os dados":
        st.markdown("### 📈 Volume de Clientes por Dia")
        
        # Preparar dados para gráfico
        dados_dia = metricas['dados_filtrados'].groupby(['data_apenas', 'atendente']).size().reset_index(name='quantidade')
        dados_pivot = dados_dia.pivot(index='data_apenas', columns='atendente', values='quantidade').fillna(0)
        
        fig_linha = go.Figure()
        
        if 'Naura' in dados_pivot.columns:
            fig_linha.add_trace(go.Scatter(
                x=dados_pivot.index,
                y=dados_pivot['Naura'],
                mode='lines+markers',
                name='Naura',
                line=dict(color='#2E8B57', width=3),
                marker=dict(size=8)
            ))
        
        if 'Diessy' in dados_pivot.columns:
            fig_linha.add_trace(go.Scatter(
                x=dados_pivot.index,
                y=dados_pivot['Diessy'],
                mode='lines+markers',
                name='Diessy',
                line=dict(color='#DC143C', width=3),
                marker=dict(size=8)
            ))
        
        fig_linha.update_layout(
            title="Evolução Diária do Volume de Atendimento",
            xaxis_title="Data",
            yaxis_title="Número de Clientes",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig_linha, use_container_width=True)
    
    # Gráfico 2: Comparativo de volume total
    st.markdown("### 📊 Comparativo de Volume Total")
    
    fig_bar = go.Figure(data=[
        go.Bar(
            x=['Naura', 'Diessy'],
            y=[metricas['naura']['total'], metricas['diessy']['total']],
            marker_color=['#2E8B57', '#DC143C'],
            text=[metricas['naura']['total'], metricas['diessy']['total']],
            textposition='auto',
        )
    ])
    
    titulo_grafico = f"Volume Total de Clientes por Atendente"
    if tipo_filtro == "Dia específico":
        titulo_grafico += f" - {data_selecionada.strftime('%d/%m/%Y')}"
    
    fig_bar.update_layout(
        title=titulo_grafico,
        yaxis_title="Número de Clientes",
        height=400
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Gráfico 3: Tempo de espera (se disponível)
    if 'faixa_tempo' in metricas['dados_filtrados'].columns:
        st.markdown("### ⏱️ Distribuição do Tempo de Espera")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Naura")
            if metricas['naura']['distribuicao_tempo']:
                fig_pie_naura = px.pie(
                    values=list(metricas['naura']['distribuicao_tempo'].values()),
                    names=list(metricas['naura']['distribuicao_tempo'].keys()),
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_pie_naura.update_layout(height=300)
                st.plotly_chart(fig_pie_naura, use_container_width=True)
            else:
                st.info("Sem dados de tempo para Naura")
        
        with col2:
            st.markdown("#### Diessy")
            if metricas['diessy']['distribuicao_tempo']:
                fig_pie_diessy = px.pie(
                    values=list(metricas['diessy']['distribuicao_tempo'].values()),
                    names=list(metricas['diessy']['distribuicao_tempo'].keys()),
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie_diessy.update_layout(height=300)
                st.plotly_chart(fig_pie_diessy, use_container_width=True)
            else:
                st.info("Sem dados de tempo para Diessy")
    
    # === SEÇÃO 6: INSIGHTS EXECUTIVOS ===
    st.markdown("## 💡 Insights Executivos")
    
    # Calcular insights
    diferenca_volume = abs(metricas['naura']['total'] - metricas['diessy']['total'])
    percentual_diferenca = (diferenca_volume / max(metricas['naura']['total'], metricas['diessy']['total'])) * 100 if max(metricas['naura']['total'], metricas['diessy']['total']) > 0 else 0
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Volume de Atendimento")
        if percentual_diferenca > 20:
            st.markdown(f"""
            <div class="alert-warning">
                <strong>⚠️ ATENÇÃO:</strong> Diferença significativa de volume entre as atendentes ({percentual_diferenca:.1f}%).
                Considere redistribuir a carga de trabalho.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert-success">
                <strong>✅ BOM:</strong> Volume equilibrado entre as atendentes (diferença: {percentual_diferenca:.1f}%).
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### ⏱️ Tempo de Resposta")
        if naura_tempo > 0 and diessy_tempo > 0:
            diferenca_tempo = abs(naura_tempo - diessy_tempo)
            if diferenca_tempo > 30:  # Mais de 30 minutos de diferença
                st.markdown(f"""
                <div class="alert-warning">
                    <strong>⚠️ ATENÇÃO:</strong> Grande diferença no tempo de resposta ({diferenca_tempo:.1f} min).
                    Revisar processos de atendimento.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="alert-success">
                    <strong>✅ BOM:</strong> Tempos de resposta similares (diferença: {diferenca_tempo:.1f} min).
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Dados de tempo de resposta não disponíveis neste arquivo.")
    
    # === SEÇÃO 7: RECOMENDAÇÕES ===
    st.markdown("## 🎯 Recomendações")
    
    recomendacoes = []
    
    # Recomendação baseada em volume
    if percentual_diferenca > 20:
        melhor = "Naura" if metricas['naura']['total'] > metricas['diessy']['total'] else "Diessy"
        pior = "Diessy" if melhor == "Naura" else "Naura"
        recomendacoes.append(f"📈 **Redistribuir leads:** {melhor} está atendendo {percentual_diferenca:.1f}% mais clientes que {pior}")
    
    # Recomendação baseada em tempo
    if naura_tempo > 0 and diessy_tempo > 0:
        if abs(naura_tempo - diessy_tempo) > 30:
            mais_rapida = "Naura" if naura_tempo < diessy_tempo else "Diessy"
            mais_lenta = "Diessy" if mais_rapida == "Naura" else "Naura"
            recomendacoes.append(f"⚡ **Treinamento:** {mais_lenta} pode melhorar tempo de resposta seguindo práticas de {mais_rapida}")
    
    # Recomendações específicas para análise diária
    if tipo_filtro == "Dia específico":
        recomendacoes.append(f"📅 **Análise diária:** Use o filtro para comparar diferentes dias e identificar padrões")
        recomendacoes.append(f"🕐 **Horários de pico:** Monitore distribuição por hora para otimizar escalas")
    
    # Recomendações gerais
    recomendacoes.append("📊 **Monitoramento:** Use filtros diários para acompanhar performance em tempo real")
    recomendacoes.append("🎯 **Meta:** Manter volume equilibrado e tempo de resposta abaixo de 30 minutos")
    recomendacoes.append("🔄 **Atualização:** Fazer upload de novos dados diariamente para acompanhar evolução")
    
    for rec in recomendacoes:
        st.markdown(f"- {rec}")
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        Dashboard gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
        <br>Sistema de Análise de Performance - Naura vs Diessy
        <br>Filtro ativo: {metricas['geral']['periodo_texto']}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

