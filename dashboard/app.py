"""
app.py - Versione corretta con gestione errori
"""
import streamlit as st
from dashboard.components import (
    render_sentiment_matrix,
    render_option_walls,
    render_alert_panel,
    render_skew_trend_chart
)

# Import condizionali per sviluppo
try:
    from analysis.skew_analyzer import SkewAnalyzer
    from analysis.pcr_analyzer import PCRAnalyzer
    from analysis.volatility_analyzer import VolatilityAnalyzer
    from data.options_fetcher import OptionsFetcher, fetch_options_snapshot
    MODULES_LOADED = True
except ImportError as e:
    st.warning(f"Alcuni moduli non trovati: {e}")
    MODULES_LOADED = False

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
        
        col1, col2 = st.columns(2)
        with col1:
            use_mock_data = st.checkbox("Usa dati mock", value=True)
        with col2:
            update_button = st.button("🔄 Aggiorna Dati")
    
    # Inizializza dati
    if 'options_data' not in st.session_state or update_button:
        if not MODULES_LOADED or use_mock_data:
            # Usa dati mock
            st.session_state.options_data = get_mock_data()
            st.info("🔧 Usando dati mock per sviluppo")
        else:
            # Prova a fetch dati reali
            try:
                fetcher = OptionsFetcher(ticker)
                options_data = fetcher.fetch_options_data(expiration)
                st.session_state.options_data = options_data
                st.success("✅ Dati caricati con successo")
            except Exception as e:
                st.error(f"❌ Errore fetch dati: {e}")
                st.session_state.options_data = get_mock_data()
                st.info("🔧 Fallback a dati mock")
    
    options_data = st.session_state.options_data
    
    # Se moduli non caricati, mostra solo dati raw
    if not MODULES_LOADED:
        st.warning("⚠️ Moduli di analisi non disponibili")
        st.json(options_data)
        return
    
    # Inizializza analizzatori
    try:
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
        skew_data = skew_analyzer.calculate_25delta_skew() or {}
        pcr_data = pcr_analyzer.calculate_all_pcr() or {}
        vol_data = vol_analyzer.analyze_volatility_regime(
            market_return=options_data.get('market_return', 0)
        ) or {}
        walls_data = skew_analyzer.generate_option_walls() or {}
        
        # Aggiungi dati di trend allo skew
        if skew_data:
            skew_data['skew_change'] = -2.1  # Mock change
            skew_data['interpretation'] = "Skew in calo in giornata ribassista → mercato scettico"
        
    except Exception as e:
        st.error(f"❌ Errore nell'analisi: {e}")
        # Fallback a dati mock per visualizzazione
        skew_data, pcr_data, vol_data, walls_data = get_mock_analysis_data(options_data)
    
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
    historical_data = get_mock_historical_data()
    render_skew_trend_chart(historical_data)
    
    # Debug info
    with st.expander("🔍 Debug Info"):
        st.write("**Dati caricati:**")
        st.json({
            'ticker': options_data.get('ticker'),
            'spot': options_data.get('spot_price'),
            'calls_count': len(options_data.get('calls', [])),
            'puts_count': len(options_data.get('puts', [])),
            'market_return': options_data.get('market_return')
        })

def get_mock_data():
    """Genera dati mock per testing"""
    import datetime
    
    calls = [
        {'strike': 350, 'open_interest': 45200, 'volume': 1200, 'implied_volatility': 0.18, 'delta': 0.4},
        {'strike': 355, 'open_interest': 38700, 'volume': 900, 'implied_volatility': 0.16, 'delta': 0.3},
        {'strike': 360, 'open_interest': 21500, 'volume': 600, 'implied_volatility': 0.15, 'delta': 0.2},
    ]
    
    puts = [
        {'strike': 340, 'open_interest': 55800, 'volume': 1500, 'implied_volatility': 0.22, 'delta': -0.4},
        {'strike': 335, 'open_interest': 42100, 'volume': 1100, 'implied_volatility': 0.24, 'delta': -0.3},
        {'strike': 330, 'open_interest': 29800, 'volume': 800, 'implied_volatility': 0.26, 'delta': -0.2},
    ]
    
    return {
        'spot_price': 345,
        'ticker': 'SPY',
        'calls': calls,
        'puts': puts,
        'volume_data': {
            'calls': {c['strike']: c['volume'] for c in calls},
            'puts': {p['strike']: p['volume'] for p in puts}
        },
        'oi_data': {
            'calls': {c['strike']: c['open_interest'] for c in calls},
            'puts': {p['strike']: p['open_interest'] for p in puts}
        },
        'vix_data': {
            'current': 18.5,
            'previous': 17.2,
            'week_ago': 16.8,
            'change': 1.3
        },
        'market_return': -1.5,
        'timestamp': datetime.datetime.now().isoformat()
    }

def get_mock_analysis_data(options_data):
    """Genera dati mock per analisi"""
    skew_data = {
        'skew_percent': 15.5,
        'skew_change': -2.1,
        'interpretation': 'Skew in calo in giornata ribassista → mercato NON crede a questo calo',
        'alert_level': 'medium'
    }
    
    pcr_data = {
        'volume': {'value': 0.85, 'interpretation': 'PCR < 1 → più call che put'},
        'open_interest': {'value': 1.45, 'fragility_alert': False},
        'systemic_fragility': {
            'alert_level': 'LOW',
            'message': 'Nessuna fragilità sistemica rilevata'
        }
    }
    
    vol_data = {
        'vix_current': 18.5,
        'vix_change': 4.2,
        'market_return': -1.5,
        'message': '🔴 VOLATILITÀ ESPLODE: Mercato in ribasso e VIX in forte rialzo',
        'is_volatility_spiking': True
    }
    
    walls_data = {
        'spot_price': options_data.get('spot_price', 345),
        'calls': [
            {'strike': 350, 'open_interest': 45200, 'distance_percent': 1.4},
            {'strike': 355, 'open_interest': 38700, 'distance_percent': 2.9}
        ],
        'puts': [
            {'strike': 340, 'open_interest': 55800, 'distance_percent': -1.4},
            {'strike': 335, 'open_interest': 42100, 'distance_percent': -2.9}
        ],
        'max_pain': 345
    }
    
    return skew_data, pcr_data, vol_data, walls_data

def get_mock_historical_data():
    """Genera dati storici mock"""
    import datetime
    data = []
    base_date = datetime.datetime.now() - datetime.timedelta(days=30)
    
    for i in range(30):
        date = base_date + datetime.timedelta(days=i)
        skew = 10 + i * 0.2 + (5 if i % 7 == 0 else 0)  # Variazione con picchi settimanali
        market_return = (i % 10 - 5) * 0.5  # Ritorni casuali tra -2.5% e +2.5%
        
        data.append({
            'timestamp': date,
            'skew_percent': skew,
            'market_return': market_return
        })
    
    return data

if __name__ == "__main__":
    main()
