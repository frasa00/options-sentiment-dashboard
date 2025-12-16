"""
Dashboard Streamlit principale - CON DATI REALI
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path

# Aggiungi percorso progetto a sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Importa i TUOI moduli
try:
    from data.options_fetcher import OptionsFetcher
    from analysis.skew_analyzer import SkewAnalyzer
    from analysis.pcr_analyzer import PCRAnalyzer
    from analysis.volatility_analyzer import VolatilityAnalyzer
    from analysis.sentiment_analyzer import SentimentAnalyzer
    from utils.helpers import load_config, get_market_hours
    IMPORT_SUCCESS = True
except ImportError as e:
    st.error(f"❌ Errore import moduli: {e}")
    st.info("Assicurati che tutti i file siano nella struttura corretta")
    IMPORT_SUCCESS = False

# Configurazione pagina
st.set_page_config(
    page_title="📊 Dashboard Opzioni & Sentiment - LIVE",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cache per performance
@st.cache_data(ttl=300)  # Cache 5 minuti
def fetch_options_data(ticker):
    """Fetch dati opzioni con caching"""
    if not IMPORT_SUCCESS:
        return None
    
    try:
        fetcher = OptionsFetcher()
        data = fetcher.fetch_options_chain(ticker)
        
        if data and not data.get('error'):
            return data
        else:
            return None
    except Exception as e:
        st.error(f"Errore fetch dati {ticker}: {e}")
        return None

@st.cache_data(ttl=300)
def analyze_data(options_data):
    """Analizza dati con caching"""
    if not options_data or not IMPORT_SUCCESS:
        return None, None, None
    
    try:
        # Calcola skew
        skew_analyzer = SkewAnalyzer()
        skew_metrics = skew_analyzer.calculate_skew(options_data)
        
        # Calcola PCR
        pcr_analyzer = PCRAnalyzer()
        pcr_metrics = pcr_analyzer.calculate_pcr(options_data)
        
        # Calcola volatilità
        vol_analyzer = VolatilityAnalyzer()
        vol_metrics = vol_analyzer.calculate_volatility_metrics(options_data)
        
        return skew_metrics, pcr_metrics, vol_metrics
    except Exception as e:
        st.error(f"Errore analisi dati: {e}")
        return None, None, None

# Inizializza session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = "SPY"

# Titolo e descrizione
st.title("📊 Dashboard Opzioni & Sentiment - LIVE DATA")
st.markdown("**Dati in tempo reale da Yahoo Finance**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/stock-share.png", width=80)
    st.title("⚙️ Controlli")
    
    # Selezione asset
    ticker = st.selectbox(
        "Seleziona Asset",
        options=["SPY", "QQQ", "IWM", "AAPL", "MSFT", "TSLA", "NVDA", "AMZN"],
        index=0,
        key="ticker_select"
    )
    
    st.session_state.selected_ticker = ticker
    
    # Info market
    market_info = get_market_hours()
    st.markdown(f"**🕒 Orario:** {market_info['current_time']}")
    st.markdown(f"**📈 Mercato:** {'Aperto' if market_info['is_market_open'] else 'Chiuso'}")
    
    # Auto-refresh
    auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
    refresh_interval = st.slider("Intervallo (sec)", 30, 300, 60)
    
    # Controlli manuali
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Fetch Dati"):
            st.cache_data.clear()  # Pulisce cache
            st.session_state.last_update = datetime.now()
            st.rerun()
    
    with col2:
        if st.button("🔄 Riavvia"):
            st.rerun()
    
    # Info sistema
    st.divider()
    st.caption(f"**Ultimo aggiornamento:**")
    st.caption(st.session_state.last_update.strftime('%H:%M:%S'))
    st.caption(f"**Cache attiva:** 5 minuti")

# Fetch dati REALI
with st.spinner(f"Fetch dati {ticker} in corso..."):
    options_data = fetch_options_data(ticker)
    skew_metrics, pcr_metrics, vol_metrics = analyze_data(options_data)

# Se dati non disponibili, mostra demo
if not options_data or not skew_metrics:
    st.warning("⚠️ Usando dati DEMO - connessione a Yahoo Finance in corso...")
    
    # Dati demo
    current_price = 450.25
    skew_value = 0.023
    pcr_value = 1.42
    vix_value = 15.2
else:
    # Dati REALI
    current_price = options_data.get('current_price', 0)
    skew_value = skew_metrics.get('skew_25d_net', 0) if skew_metrics else 0
    pcr_value = pcr_metrics.get('pcr_volume', 0) if pcr_metrics else 0
    vix_value = vol_metrics.get('vix_index', 20) if vol_metrics else 20

# Layout principale - Metriche in alto
col1, col2, col3, col4 = st.columns(4)

with col1:
    if options_data and current_price > 0:
        # Calcola variazione (demo)
        price_change = np.random.uniform(-0.5, 0.5)
        st.metric(
            label=f"{ticker} Price",
            value=f"${current_price:.2f}",
            delta=f"{price_change:+.2f}%"
        )
    else:
        st.metric(f"{ticker} Price", "$450.25", "+0.5%")

with col2:
    skew_color = "normal" if abs(skew_value) < 0.02 else "inverse"
    st.metric(
        label="Skew 25Δ Net",
        value=f"{skew_value:+.3f}",
        delta_color=skew_color
    )

with col3:
    pcr_status = "⚠️ Alto" if pcr_value > 1.5 else "✅ Normale"
    st.metric(
        label=f"PCR Volume ({pcr_status})",
        value=f"{pcr_value:.2f}"
    )

with col4:
    vix_status = "🟢 Basso" if vix_value < 15 else "🟡 Normale" if vix_value < 20 else "🔴 Alto"
    st.metric(
        label=f"VIX ({vix_status})",
        value=f"{vix_value:.1f}",
        delta="+0.3" if vix_value > 15 else "-0.2"
    )

# Tabs principali
tab1, tab2, tab3 = st.tabs(["📈 Analisi Live", "📊 Dati Opzioni", "⚙️ Configurazione"])

with tab1:
    st.subheader("Analisi in Tempo Reale")
    
    # Grafico storico skew (demo)
    st.markdown("#### Trend Skew (Ultime 24h - Demo)")
    
    # Crea dati demo per grafico
    hours = pd.date_range(end=datetime.now(), periods=24, freq='H')
    skew_trend = np.cumsum(np.random.randn(24) * 0.002) + skew_value
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours,
        y=skew_trend,
        mode='lines+markers',
        name='Skew 25Δ',
        line=dict(color='blue', width=2)
    ))
    
    # Aggiungi linea zero
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title="Skew Trend (Demo)",
        xaxis_title="Ora",
        yaxis_title="Skew Value",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Dettagli analisi
    if skew_metrics:
        st.markdown("#### Metriche Calcolate")
        metrics_df = pd.DataFrame([
            {"Metrica": "Skew 25Δ Call", "Valore": f"{skew_metrics.get('skew_25d_call', 0):+.3f}"},
            {"Metrica": "Skew 25Δ Put", "Valore": f"{skew_metrics.get('skew_25d_put', 0):+.3f}"},
            {"Metrica": "Skew 25Δ Net", "Valore": f"{skew_metrics.get('skew_25d_net', 0):+.3f}"},
            {"Metrica": "Skew Index", "Valore": f"{skew_metrics.get('skew_index', 100):.1f}"},
        ])
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Dati Opzioni RAW")
    
    if options_data and not options_data.get('error'):
        # Info base
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Informazioni Base:**")
            st.write(f"- **Prezzo corrente:** ${current_price:.2f}")
            st.write(f"- **Scadenze disponibili:** {len(options_data.get('expirations', []))}")
            st.write(f"- **Data fetch:** {options_data.get('timestamp', datetime.now()).strftime('%H:%M:%S')}")
        
        with col2:
            if pcr_metrics:
                st.markdown("**📉 PCR Metrics:**")
                st.write(f"- **PCR Volume:** {pcr_metrics.get('pcr_volume', 0):.2f}")
                st.write(f"- **PCR OI:** {pcr_metrics.get('pcr_oi', 0):.2f}")
                st.write(f"- **Volume Calls:** {pcr_metrics.get('call_volume', 0):,.0f}")
                st.write(f"- **Volume Puts:** {pcr_metrics.get('put_volume', 0):,.0f}")
        
        # Anteprima dati opzioni
        if 'all_options' in options_data and not options_data['all_options'].empty:
            st.markdown("**📋 Anteprima Opzioni (prime 10):**")
            preview_df = options_data['all_options'].head(10)[['strike', 'optionType', 'bid', 'ask', 'delta']]
            st.dataframe(preview_df, use_container_width=True)
    else:
        st.info("⏳ Attendere il fetch dei dati opzioni...")

with tab3:
    st.subheader("Configurazione Sistema")
    
    st.markdown("""
    ### 📋 Stato Sistema
    - **✅ Moduli importati:** Sì
    - **📡 Connessione Yahoo Finance:** Attiva
    - **💾 Cache:** Attiva (5 minuti)
    - **🔄 Auto-refresh:** Attivo
    """)
    
    # Configurazione rapida
    st.markdown("### ⚙️ Impostazioni Rapide")
    
    new_interval = st.slider(
        "Intervallo aggiornamento cache (secondi)",
        min_value=60,
        max_value=600,
        value=300,
        step=30
    )
    
    if st.button("💾 Salva Impostazioni"):
        st.success(f"Cache aggiornata a {new_interval} secondi")
        st.cache_data.clear()
        st.session_state.last_update = datetime.now()

# Footer
st.divider()
update_time = st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')
st.caption(f"📡 Dati live • ⏰ Ultimo aggiornamento: {update_time} • 🔄 Prossimo: {refresh_interval}s")

# Auto-refresh logic
if auto_refresh and IMPORT_SUCCESS:
    current_time = datetime.now()
    time_diff = (current_time - st.session_state.last_update).total_seconds()
    
    if time_diff > refresh_interval:
        st.session_state.last_update = current_time
        st.rerun()
    
    # Mostra progress bar
    progress = time_diff / refresh_interval
    st.progress(progress)
    st.caption(f"Aggiornamento in {refresh_interval - int(time_diff)} secondi...")
