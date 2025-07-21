#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Executivo - Naura vs Diessy
Sistema web interativo para apresentação aos responsáveis da empresa
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
import json
import os
import glob

# Configuração da página
st.set_page_config(
    page_title="Dashboard Executivo - Naura vs Diessy",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS customizado para aparência profissional
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
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #2e8b57;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
    }
    
    .alert-critical {
        background: #ffe6e6;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .alert-success {
        background: #e6ffe6;
        border-left: 4px solid #28a745;
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
    
    .comparison-loser {
        background: #ffe6e6;
        border: 2px solid #dc3545;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class DashboardExecutivo:
    def __init__(self):
        self.dados_processados = None
        self.metricas = {}
        
    def encontrar_arquivo_excel(self):
        """Encontra arquivo Excel do Octadesk"""
        arquivos_xlsx = glob.glob("*.xlsx")
        if arquivos_xlsx:
            return max(arquivos_xlsx, key=os.path.getsize)
        return None
    
    def carregar_dados(self, arquivo):
        """Carrega e processa dados do Octadesk"""
        try:
            df = pd.read_excel(arquivo)
            
            # Filtrar Naura e Diessy
            mask_naura = df['Responsável da conversa'].str.contains('Naura', case=False, na=False)
            mask_diessy = df['Responsável da conversa'].str.contains('Diessy', case=False, na=False)
            df_filtrado = df[mask_naura | mask_diessy].copy()
            
            # Processar dados
            df_filtrado['data_entrada'] = pd.to_datetime(df_filtrado['Data e hora de entrada'], format='%d/%m/%Y %H:%M', errors='coerce')
            df_filtrado['data_apenas'] = df_filtrado['data_entrada'].dt.date
            df_filtrado['atendente'] = df_filtrado['Responsável da conversa'].apply(
                lambda x: "Naura" if "naura" in str(x).lower() else "Diessy"
            )
            
            # Processar tempo de espera
            df_filtrado['tempo_espera_min'] = df_filtrado['Tempo de espera após atribuição'].apply(self.processar_tempo_espera)
            df_filtrado['faixa_tempo'] = df_filtrado['tempo_espera_min'].apply(self.classificar_faixa_tempo)
            
            self.dados_processados = df_filtrado
            return df_filtrado
            
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return None
    
    def processar_tempo_espera(self, tempo_str):
        """Converte tempo para minutos"""
        if pd.isna(tempo_str) or tempo_str == '-':
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
    
    def classificar_faixa_tempo(self, minutos):
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
    
    def calcular_metricas(self):
        """Calcula métricas para o dashboard"""
        if self.dados_processados is None:
            return {}
        
        df = self.dados_processados
        
        # Métricas gerais
        total_clientes = len(df)
        periodo_dias = df['data_apenas'].nunique()
        
        # Métricas por atendente
        metricas_naura = self.calcular_metricas_atendente(df, "Naura")
        metricas_diessy = self.calcular_metricas_atendente(df, "Diessy")
        
        # Comparativo
        melhor_volume = "Naura" if metricas_naura['total'] > metricas_diessy['total'] else "Diessy"
        melhor_tempo = self.comparar_tempo_medio(metricas_naura, metricas_diessy)
        
        self.metricas = {
            'geral': {
                'total_clientes': total_clientes,
                'periodo_dias': periodo_dias,
                'media_diaria': total_clientes / periodo_dias if periodo_dias > 0 else 0
            },
            'naura': metricas_naura,
            'diessy': metricas_diessy,
            'comparativo': {
                'melhor_volume': melhor_volume,
                'melhor_tempo': melhor_tempo
            }
        }
        
        return self.metricas
    
    def calcular_metricas_atendente(self, df, nome_atendente):
        """Calcula métricas para uma atendente"""
        df_atendente = df[df['atendente'] == nome_atendente]
        
        if len(df_atendente) == 0:
            return {'total': 0, 'media_diaria': 0, 'tempo_medio': 0, 'distribuicao_tempo': {}}
        
        total = len(df_atendente)
        dias = df_atendente['data_apenas'].nunique()
        media_diaria = total / dias if dias > 0 else 0
        
        # Tempo médio (apenas valores válidos)
        tempos_validos = df_atendente['tempo_espera_min'].dropna()
        tempo_medio = tempos_validos.mean() if len(tempos_validos) > 0 else 0
        
        # Distribuição por faixa de tempo
        distribuicao = df_atendente['faixa_tempo'].value_counts().to_dict()
        
        return {
            'total': total,
            'media_diaria': media_diaria,
            'tempo_medio': tempo_medio,
            'distribuicao_tempo': distribuicao
        }
    
    def comparar_tempo_medio(self, naura, diessy):
        """Compara tempo médio entre atendentes"""
        tempo_naura = naura['tempo_medio']
        tempo_diessy = diessy['tempo_medio']
        
        if tempo_naura == 0 and tempo_diessy == 0:
            return "Empate"
        elif tempo_naura == 0:
            return "Diessy"
        elif tempo_diessy == 0:
            return "Naura"
        else:
            return "Naura" if tempo_naura < tempo_diessy else "Diessy"

def main():
    """Função principal do dashboard"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        📊 DASHBOARD EXECUTIVO - PERFORMANCE ATENDIMENTO
        <br><small>Análise Comparativa: Naura vs Diessy</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar dashboard
    dashboard = DashboardExecutivo()
    
    # Carregar dados
    arquivo = dashboard.encontrar_arquivo_excel()
    
    if not arquivo:
        st.error("❌ Nenhum arquivo Excel do Octadesk encontrado!")
        st.info("Coloque o arquivo exportado do Octadesk na mesma pasta do script.")
        return
    
    dados = dashboard.carregar_dados(arquivo)
    
    if dados is None or len(dados) == 0:
        st.error("❌ Não foi possível carregar os dados ou nenhum registro encontrado para Naura/Diessy")
        return
    
    # Calcular métricas
    metricas = dashboard.calcular_metricas()
    
    # Informações do arquivo
    st.sidebar.markdown("### 📁 Informações do Arquivo")
    st.sidebar.info(f"""
    **Arquivo:** {arquivo}
    **Registros:** {len(dados)}
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
        melhor_volume = metricas['comparativo']['melhor_volume']
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
        melhor_tempo = metricas['comparativo']['melhor_tempo']
        if melhor_tempo == "Naura":
            tempo_naura = metricas['naura']['tempo_medio']
            st.markdown(f"""
            <div class="comparison-winner">
                <h3>⚡ MAIS RÁPIDA</h3>
                <h2>NAURA</h2>
                <p>Tempo médio: {tempo_naura:.1f} min</p>
                <p>Resposta mais ágil</p>
            </div>
            """, unsafe_allow_html=True)
        elif melhor_tempo == "Diessy":
            tempo_diessy = metricas['diessy']['tempo_medio']
            st.markdown(f"""
            <div class="comparison-winner">
                <h3>⚡ MAIS RÁPIDA</h3>
                <h2>DIESSY</h2>
                <p>Tempo médio: {tempo_diessy:.1f} min</p>
                <p>Resposta mais ágil</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="comparison-winner">
                <h3>⚡ TEMPO DE RESPOSTA</h3>
                <h2>EMPATE</h2>
                <p>Performance similar</p>
            </div>
            """, unsafe_allow_html=True)
    
    # === SEÇÃO 3: GRÁFICOS INTERATIVOS ===
    st.markdown("## 📊 Análise Visual")
    
    # Gráfico 1: Volume por dia
    st.markdown("### 📈 Volume de Clientes por Dia")
    
    # Preparar dados para gráfico
    dados_dia = dados.groupby(['data_apenas', 'atendente']).size().reset_index(name='quantidade')
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
    
    # Gráfico 3: Tempo de espera
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
            <div class="alert-critical">
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
        tempo_naura = metricas['naura']['tempo_medio']
        tempo_diessy = metricas['diessy']['tempo_medio']
        
        if tempo_naura > 0 and tempo_diessy > 0:
            diferenca_tempo = abs(tempo_naura - tempo_diessy)
            if diferenca_tempo > 30:  # Mais de 30 minutos de diferença
                st.markdown(f"""
                <div class="alert-critical">
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
    
    # === SEÇÃO 5: RECOMENDAÇÕES ===
    st.markdown("## 🎯 Recomendações")
    
    recomendacoes = []
    
    # Recomendação baseada em volume
    if percentual_diferenca > 20:
        melhor = metricas['comparativo']['melhor_volume']
        pior = "Diessy" if melhor == "Naura" else "Naura"
        recomendacoes.append(f"📈 **Redistribuir leads:** {melhor} está atendendo {percentual_diferenca:.1f}% mais clientes que {pior}")
    
    # Recomendação baseada em tempo
    if tempo_naura > 0 and tempo_diessy > 0:
        if abs(tempo_naura - tempo_diessy) > 30:
            mais_rapida = metricas['comparativo']['melhor_tempo']
            mais_lenta = "Diessy" if mais_rapida == "Naura" else "Naura"
            recomendacoes.append(f"⚡ **Treinamento:** {mais_lenta} pode melhorar tempo de resposta seguindo práticas de {mais_rapida}")
    
    # Recomendação geral
    recomendacoes.append("📊 **Monitoramento:** Acompanhar métricas diariamente para identificar tendências")
    recomendacoes.append("🎯 **Meta:** Manter volume equilibrado e tempo de resposta abaixo de 30 minutos")
    
    for rec in recomendacoes:
        st.markdown(f"- {rec}")
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        Dashboard gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
        <br>Dados baseados no arquivo: {arquivo}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

