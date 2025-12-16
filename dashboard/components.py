"""
components.py - Nuovi componenti per le analisi richieste
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_sentiment_matrix(skew_data, pcr_data, vol_data):
    """Matrice dei 4 indicatori chiave"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="SKEW (25Δ)",
            value=f"{skew_data.get('skew_percent', 0):.1f}%",
            delta=f"{skew_data.get('skew_change', 0):.1f}%",
            help="Differenza volatilità Put-Call 25-delta"
        )
        st.caption(skew_data.get('interpretation', ''))
    
    with col2:
        pcr_vol = pcr_data.get('volume', {}).get('value', 0)
        st.metric(
            label="Put/Call Volume",
            value=f"{pcr_vol:.2f}",
            delta="+0.12" if pcr_vol > 0.8 else "-0.05",
            help="Volume put vs call"
        )
        st.caption("Sotto 1: più call che put")
    
    with col3:
        pcr_oi = pcr_data.get('open_interest', {}).get('value', 0)
        delta_color = "inverse" if pcr_oi < 0.9 else "normal"
        st.metric(
            label="Put/Call OI",
            value=f"{pcr_oi:.2f}",
            delta_color=delta_color,
            help="Open Interest put vs call"
        )
        if pcr_oi < 0.9:
            st.warning("⚠️ Fragilità sistemica potenziale")
    
    with col4:
        vix = vol_data.get('vix_current', 0)
        vix_change = vol_data.get('vix_change', 0)
        st.metric(
            label="VIX",
            value=f"{vix:.1f}",
            delta=f"{vix_change:+.1f}",
            help="Indice volatilità"
        )
        st.caption(vol_data.get('message', ''))

def render_option_walls(walls_data):
    """Visualizza il muro delle opzioni"""
    
    st.subheader("📊 Muro delle Opzioni")
    
    spot_price = walls_data.get('spot_price', 0)
    calls = walls_data.get('calls', [])
    puts = walls_data.get('puts', [])
    
    # Crea grafico
    fig = go.Figure()
    
    # Aggiungi linee per put (rosse)
    for put in puts:
        fig.add_trace(go.Bar(
            x=[put['strike']],
            y=[put['open_interest']],
            name=f"PUT {put['strike']}",
            marker_color='red',
            text=f"{put['open_interest']:,} OI",
            hovertemplate="Strike: %{x}<br>OI: %{y:,}<br>Distanza: %{customdata:.1f}%",
            customdata=[put['distance_percent']]
        ))
    
    # Aggiungi linee per call (verdi)
    for call in calls:
        fig.add_trace(go.Bar(
            x=[call['strike']],
            y=[call['open_interest']],
            name=f"CALL {call['strike']}",
            marker_color='green',
            text=f"{call['open_interest']:,} OI",
            hovertemplate="Strike: %{x}<br>OI: %{y:,}<br>Distanza: %{customdata:.1f}%",
            customdata=[call['distance_percent']]
        ))
    
    # Linea prezzo spot
    fig.add_vline(
        x=spot_price,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Spot: {spot_price}",
        annotation_position="top"
    )
    
    # Linea max pain
    max_pain = walls_data.get('max_pain', 0)
    if max_pain > 0:
        fig.add_vline(
            x=max_pain,
            line_dash="dot",
            line_color="orange",
            annotation_text=f"Max Pain: {max_pain}",
            annotation_position="bottom"
        )
    
    fig.update_layout(
        title="Distribuzione Open Interest per Strike",
        xaxis_title="Strike Price",
        yaxis_title="Open Interest",
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabella riassuntiva
    st.subheader("Livelli Chiave")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Call Walls (Resistenze)**")
        for call in calls:
            st.write(f"• {call['strike']}: {call['open_interest']:,} OI "
                    f"(+{call['distance_percent']:.1f}%)")
    
    with col2:
        st.write("**Put Walls (Supporti)**")
        for put in puts:
            st.write(f"• {put['strike']}: {put['open_interest']:,} OI "
                    f"({put['distance_percent']:+.1f}%)")

def render_alert_panel(skew_analysis, pcr_analysis, vol_analysis):
    """Pannello alert combinati"""
    
    alerts = []
    
    # Alert 1: Skew vs mercato
    if skew_analysis.get('alert_level') == 'high':
        alerts.append({
            'type': 'skew_divergence',
            'title': '📉 Divergenza Skew',
            'message': skew_analysis.get('interpretation', ''),
            'severity': 'warning'
        })
    
    # Alert 2: Fragilità sistemica
    if pcr_analysis.get('systemic_fragility', {}).get('alert_level') in ['HIGH', 'CRITICAL']:
        alerts.append({
            'type': 'systemic_fragility',
            'title': '⚠️ Fragilità Sistemica',
            'message': pcr_analysis['systemic_fragility']['message'],
            'severity': 'error'
        })
    
    # Alert 3: Volatilità esplosiva
    if vol_analysis.get('is_volatility_spiking', False):
        alerts.append({
            'type': 'volatility_spike',
            'title': '🔴 Esplosione Volatilità',
            'message': vol_analysis.get('message', ''),
            'severity': 'error'
        })
    
    # Visualizza alert
    if alerts:
        st.subheader("🚨 Alert Attivi")
        for alert in alerts:
            if alert['severity'] == 'error':
                st.error(f"**{alert['title']}**: {alert['message']}")
            elif alert['severity'] == 'warning':
                st.warning(f"**{alert['title']}**: {alert['message']}")
            else:
                st.info(f"**{alert['title']}**: {alert['message']}")
    else:
        st.success("✅ Nessun alert critico rilevato")

def render_skew_trend_chart(historical_data):
    """Grafico storico skew"""
    
    if not historical_data or len(historical_data) < 2:
        st.info("Dati storici insufficienti")
        return
    
    dates = [d['timestamp'] for d in historical_data]
    skew_values = [d['skew_percent'] for d in historical_data]
    market_returns = [d.get('market_return', 0) for d in historical_data]
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Skew line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=skew_values,
            name="Skew %",
            line=dict(color='blue', width=2)
        ),
        secondary_y=False
    )
    
    # Market return bars
    colors = ['red' if r < 0 else 'green' for r in market_returns]
    fig.add_trace(
        go.Bar(
            x=dates,
            y=market_returns,
            name="Ritorno Mercato %",
            marker_color=colors,
            opacity=0.3
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title="Skew vs Performance Mercato",
        xaxis_title="Data",
        height=300
    )
    
    fig.update_yaxes(title_text="Skew %", secondary_y=False)
    fig.update_yaxes(title_text="Ritorno Mercato %", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
