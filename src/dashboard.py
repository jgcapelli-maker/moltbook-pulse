import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from dotenv import load_dotenv
import json

# --- CONFIG E CSS (Bloomberg Style) ---
st.set_page_config(page_title="Moltbook Terminal", page_icon="⚡", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #000000; }
    div[data-testid="metric-container"] { background-color: #111; border-left: 3px solid #333; padding: 10px; }
    h1, h2, h3, p, span { color: #e0e0e0 !important; font-family: 'Roboto Mono', monospace; }
    .evidence-box { background-color: #0a0a0a; border: 1px solid #333; padding: 15px; border-radius: 5px; font-style: italic; color: #00ffcc !important; }
    .top-list { background-color: #111; padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO ---
load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

@st.cache_resource
def get_data():
    response = supabase.table('market_pulse').select("*").order('created_at', desc=True).limit(100).execute()
    if not response.data: return pd.DataFrame()
    df = pd.DataFrame(response.data)
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('America/Sao_Paulo')
    return df

# --- UI ---
st.markdown("## ⚡ CRYPTO TREND SNIPER // TERMINAL")
if st.button('🔄 REFRESH SIGNAL'): st.cache_resource.clear(); st.rerun()

df = get_data()
if df.empty: st.info("📡 Aguardando dados..."); st.stop()

latest = df.iloc[0]
score = latest['sentiment_score']

# 1. KPI HEADER
signal = "STRONG BUY 🔥" if score > 7 else "WAIT / NEUTRAL ✋" if score > 3 else "EXTREME FEAR 🩸"
sig_color = "#00ff00" if score > 7 else "#ffff00" if score > 3 else "#ff0000"

c1, c2, c3 = st.columns([2, 1, 1])
c1.markdown(f"<div style='padding:15px; border:2px solid {sig_color}; text-align:center'><h1 style='color:{sig_color};margin:0'>{signal}</h1><h3 style='margin:0'>Target: {latest['symbol']}</h3></div>", unsafe_allow_html=True)
c2.metric("HYPE SCORE (0-10)", f"{score:.1f}")
c3.metric("PRICE MOVE (1h)", f"{latest['price_change']*100:.2f}%", delta=f"{latest['price_change']*100:.2f}%")

st.markdown("---")

# 2. ÁREA DE INTELIGÊNCIA (NOVO!)
c_left, c_right = st.columns([2, 1])

with c_left:
    st.markdown("### 🗣️ Evidência da Colmeia (Raw Data)")
    evidence = latest.get('evidence_text', 'Nenhuma evidência capturada.')
    st.markdown(f"<div class='evidence-box'>“{evidence}”</div>", unsafe_allow_html=True)
    st.caption(f"Detectado em: {latest['created_at'].strftime('%H:%M:%S')}")

with c_right:
    st.markdown("### 🏆 Top Tendências (Fresh)")
    top_json = latest.get('top_mentions')
    if top_json:
        st.write(pd.DataFrame(list(top_json.items()), columns=['Ticker', 'Menções']).set_index('Ticker'))
    else:
        st.write("Sem dados de top mentions.")

st.markdown("---")

# 3. GRÁFICO DE CORRELAÇÃO (Fundo Hype vs Linha Preço)
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=df['created_at'], y=df['sentiment_score'], name="Hype (Score)", fill='tozeroy', line=dict(color='rgba(0,255,204,0.2)', width=1)), secondary_y=False)
fig.add_trace(go.Scatter(x=df['created_at'], y=df['price_change'], name="Price %", line=dict(color='#ff0055', width=2)), secondary_y=True)
fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20,20,20,1)', font={'color':'#aaa'}, margin=dict(t=20,b=20,l=0,r=0), hovermode="x unified", legend=dict(orientation="h", y=1.1))
fig.update_yaxes(title="Score", secondary_y=False, showgrid=False); fig.update_yaxes(title="Price %", secondary_y=True, gridcolor='#333')
st.plotly_chart(fig, use_container_width=True)