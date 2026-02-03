import pandas as pd
from engine.pulse_engine import MoltPulseEngine
from database import MoltDatabase
from engine.hive_scraper import HiveScraper
import requests
import matplotlib.pyplot as plt
import os
import time
import numpy as np
from datetime import datetime, timedelta
from flask import Flask
import threading

# --- PARTE 1: O SERVIDOR FALSO (Para o Render não desligar) ---
server = Flask(__name__)

@server.route('/')
def home():
    return "Moltbook Pulse is Alive & Scanning! 🤖"

def run_web_server():
    # Pega a porta que o Render der ou usa 10000
    port = int(os.environ.get("PORT", 10000))
    server.run(host="0.0.0.0", port=port)

# --- PARTE 2: O ROBÔ REAL ---
class MoltbookApp:
    def __init__(self):
        self.engine = MoltPulseEngine()
        self.db = MoltDatabase() 
        self.hive = HiveScraper()

    def fetch_price(self, symbol):
        clean_symbol = symbol.replace('$', '') + "USDT"
        print(f"📉 CHECK: Buscando preço para {clean_symbol}...")
        
        urls = [
            "https://api.binance.us/api/v3/klines", 
            "https://api.binance.com/api/v3/klines"
        ]
        
        for url in urls:
            try:
                params = {'symbol': clean_symbol, 'interval': '1m', 'limit': 60}
                r = requests.get(url, params=params, timeout=3)
                data = r.json()
                
                if isinstance(data, dict) and ('code' in data or 'msg' in data):
                    continue 

                df = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'vol', 'ct', 'qa', 'n', 'tb', 'tqa', 'i'])
                df['ts'] = pd.to_datetime(df['ts'], unit='ms')
                df['close'] = df['close'].astype(float)
                return df
            except: continue
        
        # Fallback (Dados Sintéticos)
        print("   ⚠️ Gerando dados sintéticos (Geo-fence fallback).")
        dates = [datetime.now() - timedelta(minutes=i) for i in range(60)]
        dates.reverse()
        prices = [100 + (i * 0.05) + np.random.normal(0, 0.2) for i in range(60)] 
        return pd.DataFrame({'ts': dates, 'close': prices})

    def run(self):
        while True:
            print(f"\n--- CICLO INICIADO: {datetime.now()} ---")
            try:
                trending_list = self.hive.scan_hive()
                
                if trending_list:
                    top_gem = trending_list[0][0]
                    mentions = trending_list[0][1]
                else:
                    top_gem = "BTC" # Fallback
                    mentions = 5

                print(f"🔥 ALVO: ${top_gem} ({mentions} menções)")

                df = self.fetch_price(top_gem)
                
                pulse_score = min(mentions * 0.5, 5.0)
                price_change = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
                is_lag = mentions >= 3 and abs(price_change) < 0.01
                
                if self.db:
                    self.db.save_signal(f"${top_gem}", pulse_score, price_change, is_lag)
                    
                self.generate_visual(df, top_gem, mentions, is_lag)
                print(f"🏁 CICLO CONCLUÍDO. Dormindo por 1 hora...")

            except Exception as e:
                print(f"❌ ERRO CRÍTICO NO LOOP: {e}")
            
            time.sleep(3600) 

    def generate_visual(self, df, symbol, mentions, is_lag):
        try:
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(10,5))
            ax.plot(df['ts'], df['close'], color='#00ffcc', linewidth=2)
            plt.title(f"MOLTBOOK HIVE MIND: ${symbol}\nMentions: {mentions} | Lag: {is_lag}", color='white')
            output_dir = os.path.join("data", "outputs")
            os.makedirs(output_dir, exist_ok=True)
            plt.savefig(os.path.join(output_dir, "latest_signal.png"))
            plt.close()
        except: pass

if __name__ == "__main__":
    # 1. Inicia o Servidor Falso em uma thread paralela (background)
    t = threading.Thread(target=run_web_server)
    t.daemon = True # Morre se o programa principal morrer
    t.start()
    
    print("🌍 FAKE SERVER INICIADO (Para manter o Render vivo)")

    # 2. Inicia o Robô Principal
    app = MoltbookApp()
    app.run()