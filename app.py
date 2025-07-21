#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Executivo - Naura vs Diessy (Versão Streamlit Cloud)
Sistema web interativo para apresentação aos responsáveis da empresa
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import io

# Configuração da página
st.set_page_config(
    page_title="Dashboard Executivo - Naura vs Diessy",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
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

def calcular_metricas(df):
    """Calcula métricas para o dashboard"""
    if df is None or len(df) == 0:
        return {}
    
    # Métricas gerais
    total_clientes = len(df)
    periodo_dias = df['data_apenas'].nunique()
    data_inicio = df['data_apenas'].min()
    data_fim = df['data_apenas'].max()
    
    # Métricas por atendente
    naura_df = df[df['atendente'] == 'Naura']
    diessy_df = df[df['atendente'] == 'Diessy']
    
    naura_total = len(naura_df)
    diessy_total = len(diessy_df)
    
    naura_media = naura_total / periodo_dias if periodo_dias > 0 else 0
    diessy_media = diessy_total / periodo_dias if periodo_dias > 0 else 0
    
    # Tempo médio (se disponível)
    naura_tempo = 0
    diessy_tempo = 0
    
    if 'tempo_espera_min' in df.columns:
        naura_tempos = naura_df['tempo_espera_min'].dropna()
        diessy_tempos = diessy_df['tempo_espera_min'].dropna()
        
        naura_tempo = naura_tempos.mean() if len(naura_tempos) > 0 else 0
        diessy_tempo = diessy_tempos.mean() if len(diessy_tempos) > 0 else 0
    
    # Distribuição por faixa de tempo
    naura_dist = {}
    diessy_dist = {}
    
    if 'faixa_tempo' in df.columns:
        naura_dist = naura_df['faixa_tempo'].value_counts().to_dict()
        diessy_dist = diessy_df['faixa_tempo'].value_counts().to_dict()
    
    return {
        'geral': {
            'total_clientes': total_clientes,
            'periodo_dias': periodo_dias,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'media_diaria': total_clientes / periodo_dias if periodo_dias > 0 else 0
        },
        'naura': {
            'total': naura_total,
            'media_diaria': naura_media,
            'tempo_medio': naura_tempo,
            'distribuicao_tempo': naura_dist
        },
        'diessy': {
            'total': diessy_total,
            'media_diaria': diessy_media,
            'tempo_medio': diessy_tempo,
            'distribuicao_tempo': diessy_dist
        }
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
    
    # Upload de arquivo
    st.markdown("## 📁 Upload do Arquivo do Octadesk")
    
    uploaded_file = st.file_uploader(
        "Escolha o arquivo Excel exportado do Octadesk",
        type=['xlsx', 'xls'],
        help="Faça upload do arquivo de conversas exportado do Octadesk"
    )
    
    if uploaded_file is None:
        st.info("👆 Faça upload do arquivo Excel do Octadesk para começar a análise")
        st.markdown("""
        ### 📋 Como exportar do Octadesk:
        1. Acesse o Octadesk
        2. Vá em **Relatórios**
        3. Selecione **Total de conversas**
        4. Escolha o período desejado
        5. Clique em **Exportar** → **Excel**
        6. Faça upload do arquivo aqui
        """)
        return
    
    # Carregar dados
    try:
        df = pd.read_excel(uploaded_file)
        st.success(f"✅ Arquivo carregado: {len(df)} registros encontrados")
    except Exception as e:
        st.error(f"❌ Erro ao carregar arquivo: {e}")
        return
    
    # Processar dados
    dados_processados = processar_dados(df)
    
    if dados_processados is None or len(dados_processados) == 0:
        st.error("❌ Nenhum dado encontrado para Naura ou Diessy")
        st.info("Verifique se o arquivo contém dados das atendentes Naura e Diessy")
        return
    
    # Calcular métricas
    metricas = calcular_metricas(dados_processados)
    
    # Informações do arquivo
    st.sidebar.markdown("### 📁 Informações do Arquivo")
    st.sidebar.info(f"""
    **Registros totais:** {len(df)}
    **Naura + Diessy:** {len(dados_processados)}
    **Período:** {metricas['geral']['periodo_dias']} dias
    **Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """)
    
    # === SEÇÃO 1: MÉTRICAS PRINCIPAIS ===
    st.markdown("## 📈 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total de Clientes",
            value=f"{metricas['geral']['total_clientes']:,}",
            delta=f"Período: {metricas['geral']['periodo_dias']} dias"
        )
    
    with col2:
        st.metric(
            label="Média Diária",
            value=f"{metricas['geral']['media_diaria']:.1f}",
            delta="clientes/dia"
        )
    
    with col3:
        st.metric(
            label="Clientes Naura",
            value=f"{metricas['naura']['total']:,}",
            delta=f"{metricas['naura']['media_diaria']:.1f}/dia"
        )
    
    with col4:
        st.metric(
            label="Clientes Diessy", 
            value=f"{metricas['diessy']['total']:,}",
            delta=f"{metricas['diessy']['media_diaria']:.1f}/dia"
        )
    
    # === SEÇÃO 2: COMPARATIVO EXECUTIVO ===
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
    
    # === SEÇÃO 3: GRÁFICOS INTERATIVOS ===
    st.markdown("## 📊 Análise Visual")
    
    # Gráfico 1: Volume por dia
    st.markdown("### 📈 Volume de Clientes por Dia")
    
    # Preparar dados para gráfico
    dados_dia = dados_processados.groupby(['data_apenas', 'atendente']).size().reset_index(name='quantidade')
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
    
    fig_bar.update_layout(
        title="Volume Total de Clientes por Atendente",
        yaxis_title="Número de Clientes",
        height=400
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Gráfico 3: Tempo de espera (se disponível)
    if 'faixa_tempo' in dados_processados.columns:
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
    
    # === SEÇÃO 4: INSIGHTS EXECUTIVOS ===
    st.markdown("## 💡 Insights Executivos")
    
    # Calcular insights
    diferenca_volume = abs(metricas['naura']['total'] - metricas['diessy']['total'])
    percentual_diferenca = (diferenca_volume / max(metricas['naura']['total'], metricas['diessy']['total'])) * 100
    
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
    
    # === SEÇÃO 5: RECOMENDAÇÕES ===
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
    
    # Recomendações gerais
    recomendacoes.append("📊 **Monitoramento:** Acompanhar métricas diariamente para identificar tendências")
    recomendacoes.append("🎯 **Meta:** Manter volume equilibrado e tempo de resposta abaixo de 30 minutos")
    recomendacoes.append("🔄 **Atualização:** Fazer upload de novos dados semanalmente para acompanhar evolução")
    
    for rec in recomendacoes:
        st.markdown(f"- {rec}")
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        Dashboard gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
        <br>Sistema de Análise de Performance - Naura vs Diessy
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

