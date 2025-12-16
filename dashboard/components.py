"""
Componenti riutilizzabili per il dashboard
"""

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def create_skew_chart(skew_data: pd.DataFrame) -> go.Figure:
    """Crea grafico skew"""
    fig = go.Figure()
    
    if not skew_data.empty and 'skew_25d_net' in skew_data.columns:
        fig.add_trace(go.Scatter(
            x=skew_data.index,
            y=skew_data['skew_25d_net'],
            mode='lines',
            name='Skew 25Δ Net',
            line=dict(color='blue', width=2)
        ))
    
    fig.update_layout(
        title='Skew Trend',
        xaxis_title='Time',
        yaxis_title='Skew Value',
        height=300
    )
    
    return fig

def create_pcr_chart(pcr_data: pd.DataFrame) -> go.Figure:
    """Crea grafico PCR"""
    fig = go.Figure()
    
    if not pcr_data.empty and 'pcr_volume' in pcr_data.columns:
        fig.add_trace(go.Scatter(
            x=pcr_data.index,
            y=pcr_data['pcr_volume'],
            mode='lines',
            name='PCR Volume',
            line=dict(color='red', width=2)
        ))
    
    fig.update_layout(
        title='Put/Call Ratio Trend',
        xaxis_title='Time',
        yaxis_title='PCR',
        height=300
    )
    
    return fig

def create_sentiment_gauge(sentiment_score: float) -> go.Figure:
    """Crea gauge chart per sentiment"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sentiment_score * 100,
        title={'text': "Sentiment Score"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [-100, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [-100, -50], 'color': "red"},
                {'range': [-50, 0], 'color': "lightcoral"},
                {'range': [0, 50], 'color': "lightgreen"},
                {'range': [50, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': sentiment_score * 100
            }
        }
    ))
    
    fig.update_layout(height=250)
    return fig

def display_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Display a metric card"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader(title)
        st.markdown(f"## {value}")
    
    with col2:
        if delta:
            if delta_color == "inverse":
                st.metric("", "", delta)
            else:
                st.metric("", "", delta)

def create_alert(message: str, alert_type: str = "info"):
    """Crea un alert stilizzato"""
    colors = {
        "success": "🟢",
        "warning": "🟡", 
        "error": "🔴",
        "info": "🔵"
    }
    
    icon = colors.get(alert_type, "ℹ️")
    
    st.markdown(f"""
    <div style="
        background-color: {'#e8f5e9' if alert_type == 'success' else 
                         '#fff3e0' if alert_type == 'warning' else
                         '#ffebee' if alert_type == 'error' else '#e3f2fd'};
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid;
        border-color: {'#4caf50' if alert_type == 'success' else
                      '#ff9800' if alert_type == 'warning' else
                      '#f44336' if alert_type == 'error' else '#2196f3'};
        margin: 10px 0;
    ">
        <strong>{icon} {alert_type.title()}:</strong> {message}
    </div>
    """, unsafe_allow_html=True)
