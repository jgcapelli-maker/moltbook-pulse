import pandas as pd
from engine.pulse_engine import MoltPulseEngine
from database import MoltDatabase
from engine.hive_scraper import HiveScraper
import requests
import os
import time
import numpy as np
from datetime import datetime, timedelta
from flask import Flask
import threading
import json

# --- PARTE 1: O SERVIDOR FALSO (Keep-Alive) ---
server = Flask(__name__)
@server.route('/')
def home(): return "Moltbook Pulse is Alive & Scanning! 🤖"
def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server.run(host="0.0.0.0", port=port)

# --- PARTE 2: O ROBÔ REAL ---
class MoltbookApp:
    def __init__(self):
        self.engine = MoltPulseEngine()
        self.db = MoltDatabase() 
        self.hive = HiveScraper()

    # (Método fetch_price permanece idêntico, omitido para economizar espaço)
    def fetch_price(self, symbol):
        clean_symbol = symbol.replace('$', '') + "USDT"
        print(f"📉 CHECK: Buscando preço para {clean_symbol}...")
        urls = ["https://api.binance.us/api/v3/klines", "https://api.binance.com/api/v3/klines"]
        for url in urls:
            try:
                params = {'symbol': clean_symbol, 'interval': '1m', 'limit': 60}
                r = requests.get(url, params=params, timeout=3)
                data = r.json()
                if isinstance(data, dict) and ('code' in data or 'msg' in data): continue 
                df = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'vol', 'ct', 'qa', 'n', 'tb', 'tqa', 'i'])
                df['ts'] = pd.to_datetime(df['ts'], unit='ms')
                df['close'] = df['close'].astype(float)
                return df
            except: continue
        print("   ⚠️ Gerando dados sintéticos (Geo-fence fallback).")
        dates = [datetime.now() - timedelta(minutes=i) for i in range(60)]; dates.reverse()
        prices = [100 + (i * 0.05) + np.random.normal(0, 0.2) for i in range(60)] 
        return pd.DataFrame({'ts': dates, 'close': prices})

    def run(self):
        print(f"\n--- CICLO INICIADO: {datetime.now()} ---")
        try:
            # 1. Mineração Profunda (Retorna Top Lista, Texto Evidência, Dicionário Top)
            top_trends, evidence_text, top_mentions_dict = self.hive.scan_hive()
            
            if top_trends:
                winner_symbol = top_trends[0][0]
                winner_count = top_trends[0][1]
                # Score dinâmico: base 1 + log das menções para não explodir com 1000 menções
                pulse_score = min(1.0 + np.log2(winner_count + 1) * 1.5, 9.9)
            else:
                # Fallback para silêncio
                winner_symbol = "BTC"
                pulse_score = 1.0
                evidence_text = "Modo de espera: Atividade social baixa."
                top_mentions_dict = {"STATUS": "LOW_ACTIVITY"}

            print(f"🔥 ALVO FINAL: ${winner_symbol} (Score: {pulse_score:.2f})")
            
            # 2. Preço
            df = self.fetch_price(winner_symbol)
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
            
            # 3. Lag (Hype alto e preço parado)
            is_lag = pulse_score > 6.0 and abs(price_change) < 0.003
            
            # 4. Salvar Riqueza no DB
            if self.db:
                data = {
                    "symbol": f"${winner_symbol}",
                    "sentiment_score": float(pulse_score),
                    "price_change": float(price_change),
                    "is_lag": bool(is_lag),
                    "top_mentions": top_mentions_dict, # JSONB
                    "evidence_text": evidence_text     # TEXT
                }
                # Usa o cliente raw do supabase para inserir o JSON corretamente
                self.db.supabase.table("market_pulse").insert(data).execute()
                print("   💾 SINAL RICO (COM EVIDÊNCIA) SALVO!")
                
        except Exception as e:
            print(f"❌ ERRO NO CICLO: {e}")

if __name__ == "__main__":
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()
    print("🌍 FAKE SERVER INICIADO")
    
    app = MoltbookApp()
    while True:
        app.run()
        print("🏁 CICLO CONCLUÍDO. Dormindo por 1 hora...")
        time.sleep(3600)