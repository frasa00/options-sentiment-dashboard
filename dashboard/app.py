"""
app.py - Integrazione nuove funzionalità
"""
import streamlit as st
from dashboard.components import (
    render_sentiment_matrix,
    render_option_walls,
    render_alert_panel,
    render_skew_trend_chart
)
from analysis.skew_analyzer import SkewAnalyzer
from analysis.pcr_analyzer import PCRAnalyzer
from analysis.volatility_analyzer import VolatilityAnalyzer
from data.options_fetcher import OptionsFetcher

def main():
    st.set_page_config(
        page_title="Options Sentiment Dashboard",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📊 Options Sentiment Dashboard")
    st.markdown("### Analisi SKEW, PCR e Sentiment di Mercato")
    
    # Sidebar configurazione
    with st.sidebar:
        st.header("Configurazione")
        ticker = st.text_input("Ticker", value="SPY")
        expiration = st.selectbox("Scadenza", ["2024-01-19", "2024-01-26", "2024-02-02"])
        update_button = st.button("🔄 Aggiorna Dati")
    
    # Fetch dati (semplificato)
    if update_button or 'data' not in st.session_state:
        fetcher = OptionsFetcher(ticker)
        options_data = fetcher.fetch_options_data(expiration)
        st.session_state.data = options_data
    
    # Inizializza analizzatori
    options_data = st.session_state.data
    
    skew_analyzer = SkewAnalyzer(options_data)
    pcr_analyzer = PCRAnalyzer(
        volume_data=options_data.get('volume_data', {}),
        oi_data=options_data.get('oi_data', {})
    )
    vol_analyzer = VolatilityAnalyzer(
        vix_data=options_data.get('vix_data', {}),
        historical_vol=options_data.get('historical_vol', {})
    )
    
    # Calcoli
    skew_data = skew_analyzer.calculate_25delta_skew()
    pcr_data = pcr_analyzer.calculate_all_pcr()
    vol_data = vol_analyzer.analyze_volatility_regime(
        market_return=options_data.get('market_return', 0)
    )
    walls_data = skew_analyzer.generate_option_walls()
    
    # SEZIONE 1: Matrice indicatori
    st.header("1️⃣ Indicatori di Sentiment")
    render_sentiment_matrix(skew_data, pcr_data, vol_data)
    
    # SEZIONE 2: Muro opzioni
    st.header("2️⃣ Muro delle Opzioni")
    render_option_walls(walls_data)
    
    # SEZIONE 3: Alert panel
    st.header("3️⃣ Sistema di Allerta")
    render_alert_panel(skew_data, pcr_data, vol_data)
    
    # SEZIONE 4: Trend storico skew
    st.header("4️⃣ Analisi Trend Skew")
    # Ottieni dati storici (da implementare nel database)
    historical_data = []  # Sostituisci con dati reali
    render_skew_trend_chart(historical_data)
    
    # SEZIONE 5: Dettagli analisi
    with st.expander("📋 Dettagli Analisi"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Analisi Skew")
            st.json(skew_data)
            
            st.subheader("Put/Call Analysis")
            st.write("**Volume:**", pcr_data.get('volume', {}))
            st.write("**Open Interest:**", pcr_data.get('open_interest', {}))
        
        with col2:
            st.subheader("Analisi Volatilità")
            st.json(vol_data)
            
            st.subheader("Fragilità Sistemica")
            fragility = pcr_data.get('systemic_fragility', {})
            st.write(f"Livello: {fragility.get('alert_level', 'N/A')}")
            st.write(f"Messaggio: {fragility.get('message', 'N/A')}")

if __name__ == "__main__":
    main()
