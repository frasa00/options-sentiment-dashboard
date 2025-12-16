"""
Dashboard Streamlit principale - Interfaccia utente
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import sys
from pathlib import Path

# Configurazione pagina
st.set_page_config(
    page_title="📊 Dashboard Opzioni & Sentiment - frasa00",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titolo e descrizione
st.title("📊 Dashboard Opzioni & Sentiment di frasa00")
st.markdown("**Monitoraggio in tempo reale di Skew, PCR, Volatilità e Sentiment**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/stock-share.png", width=80)
    st.title("⚙️ Controlli")
    
    # Selezione asset
    ticker = st.selectbox(
        "Seleziona Asset",
        options=["SPY", "QQQ", "IWM", "AAPL", "MSFT", "TSLA", "NVDA", "AMZN"],
        index=0
    )
    
    # Auto-refresh
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    refresh_interval = st.slider("Intervallo (sec)", 30, 300, 60)
    
    # Fonti sentiment
    st.subheader("🧠 Fonti Sentiment")
    show_telegram = st.checkbox("Mostra Telegram", value=True)
    show_news = st.checkbox("Mostra News", value=True)
    
    # Controlli manuali
    if st.button("🔄 Aggiorna Ora"):
        st.session_state.force_refresh = True
        st.rerun()
    
    # Info sistema
    st.divider()
    st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")

# Layout principale - Metriche in alto
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label=f"{ticker} Price",
        value="$450.25",
        delta="+0.5%"
    )

with col2:
    st.metric(
        label="Skew 25Δ",
        value="+2.3%",
        delta_color="off"
    )

with col3:
    st.metric(
        label="PCR Volume",
        value="1.42"
    )

with col4:
    st.metric(
        label="VIX",
        value="15.2",
        delta="+0.3"
    )

# Tabs principali
tab1, tab2, tab3, tab4 = st.tabs(["📈 Skew Analysis", "📊 PCR & Vol", "🧠 Sentiment", "🔔 Signals"])

with tab1:
    st.subheader("Analisi Skew")
    # Grafico skew di esempio
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[0.9, 0.95, 1.0, 1.05, 1.1],
        y=[0.22, 0.20, 0.18, 0.19, 0.21],
        mode='lines+markers',
        name='IV Curve'
    ))
    fig.update_layout(
        title="Volatility Smile",
        xaxis_title="Moneyness (Strike/Spot)",
        yaxis_title="Implied Volatility",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Dati skew
    skew_data = pd.DataFrame({
        'Metric': ['Skew 25Δ Call', 'Skew 25Δ Put', 'Skew 25Δ Net', 'Skew Index'],
        'Value': ['+1.8%', '+2.3%', '+0.5%', '132.5'],
        'Interpretazione': ['Normale', 'Elevato', 'Leggermente Bearish', 'Rischio Alto']
    })
    st.dataframe(skew_data, use_container_width=True)

with tab2:
    st.subheader("Put/Call Ratio & Volatilità")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("PCR Volume", "1.42", "+0.12")
        st.metric("PCR OI", "1.18", "-0.04")
        
        pcr_history = pd.DataFrame({
            'Time': ['09:30', '10:00', '10:30', '11:00', '11:30'],
            'PCR': [1.32, 1.35, 1.38, 1.40, 1.42]
        })
        st.line_chart(pcr_history.set_index('Time'))
    
    with col2:
        st.metric("VIX", "15.2", "+0.5")
        st.metric("IV Mean", "18.5%", "-0.3%")
        
        vol_data = pd.DataFrame({
            'Strike': [440, 445, 450, 455, 460],
            'IV': [0.22, 0.20, 0.185, 0.19, 0.21]
        })
        st.bar_chart(vol_data.set_index('Strike'))

with tab3:
    st.subheader("Analisi Sentiment")
    
    if show_telegram:
        st.markdown("#### 📱 Telegram Sources")
        
        telegram_data = pd.DataFrame({
            'Source': ['Giardino Tartaruga', 'Marco Casario'],
            'Messages (24h)': [42, 18],
            'Sentiment': ['Mod. Bullish', 'Neutral'],
            'Key Topics': ['buy, breakout', 'analysis, support']
        })
        st.dataframe(telegram_data, use_container_width=True)
    
    if show_news:
        st.markdown("#### 📰 News Sources")
        
        news_data = pd.DataFrame({
            'Source': ['Reuters', 'Bloomberg', 'MarketWatch'],
            'Articles': [12, 8, 15],
            'Avg Sentiment': [-0.3, 0.1, -0.2],
            'Top Ticker': ['SPY', 'AAPL', 'TSLA']
        })
        st.dataframe(news_data, use_container_width=True)
    
    # Grafico sentiment
    sentiment_history = pd.DataFrame({
        'Hour': ['09:00', '10:00', '11:00', '12:00', '13:00'],
        'Score': [-0.2, -0.1, 0.0, -0.3, -0.35]
    })
    st.line_chart(sentiment_history.set_index('Hour'))

with tab4:
    st.subheader("🔔 Segnali Trading")
    
    # Segnali attivi
    signals = pd.DataFrame({
        'Signal': ['Skew Elevated', 'PCR High', 'VIX Rising', 'Sentiment Bearish'],
        'Direction': ['Caution', 'Hedge', 'Volatility', 'Reduce'],
        'Strength': ['Medium', 'High', 'Low', 'Medium'],
        'Confidence': ['75%', '82%', '65%', '70%']
    })
    
    for idx, row in signals.iterrows():
        if row['Strength'] == 'High':
            st.error(f"**{row['Signal']}**: {row['Direction']} (Conf: {row['Confidence']})")
        elif row['Strength'] == 'Medium':
            st.warning(f"**{row['Signal']}**: {row['Direction']} (Conf: {row['Confidence']})")
        else:
            st.info(f"**{row['Signal']}**: {row['Direction']} (Conf: {row['Confidence']})")
    
    st.divider()
    st.markdown("#### 📋 Tutti i Segnali")
    st.dataframe(signals, use_container_width=True)

# Footer
st.divider()
st.caption(f"Dashboard Opzioni & Sentiment • frasa00 • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Auto-refresh logic
if auto_refresh:
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    current_time = time.time()
    if current_time - st.session_state.last_refresh > refresh_interval:
        st.session_state.last_refresh = current_time
        st.rerun()
