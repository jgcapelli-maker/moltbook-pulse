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

# --- SERVER KEEP-ALIVE ---
server = Flask(__name__)
@server.route('/')
def home(): return "Moltbook Pulse SOTA is Active 🧠"
def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server.run(host="0.0.0.0", port=port)

# --- APP ---
class MoltbookApp:
    def __init__(self):
        self.engine = MoltPulseEngine()
        self.db = MoltDatabase() 
        self.hive = HiveScraper()

    def fetch_price(self, symbol):
        # 1. Filtro de Narrativa: Se tiver espaço (Ex: "AI AGENTS"), não é ticker.
        if " " in symbol: 
            return None
            
        # 2. Limpeza do Símbolo
        clean_symbol = symbol.replace('$', '').upper()
        
        # Mapa de correlação (Narrativas comuns -> Tokens líderes)
        # Isso ajuda a achar preço mesmo quando falam só o nome
        map_sym = {
            "BITCOIN": "BTC", "ETHEREUM": "ETH", "SOLANA": "SOL", 
            "DOGE": "DOGE", "PEPE": "PEPE", "WIF": "WIF"
        }
        clean_symbol = map_sym.get(clean_symbol, clean_symbol)
        
        # Se o símbolo ficou muito longo (>6 chars) e não é conhecido, provável que não seja par USDT
        if len(clean_symbol) > 8: 
            return None

        clean_symbol += "USDT"
        
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {'symbol': clean_symbol, 'interval': '1m', 'limit': 60}
            r = requests.get(url, params=params, timeout=2)
            
            if r.status_code != 200: return None
            
            data = r.json()
            # Validação extra da resposta
            if not isinstance(data, list): return None
            
            df = pd.DataFrame(data, columns=['ts', 'o', 'h', 'l', 'c', 'v', 'ct', 'qa', 'n', 'tb', 'tqa', 'i'])
            return float(df['c'].iloc[-1]), float(df['c'].iloc[-10]) # Preço atual, Preço 10min atrás
        except: 
            return None

    def run(self):
        print(f"\n--- CICLO SOTA INICIADO: {datetime.now()} ---")
        try:
            # Chama o novo Scraper Potente
            top_trends, evidence, top_dict = self.hive.scan_hive()
            
            if not top_trends:
                print("   💤 Rede em silêncio absoluto.")
                return

            winner = top_trends[0][0] # Pode ser "$BTC" ou "AI AGENTS"
            count = top_trends[0][1]
            
            # Score Logarítmico (Suaviza picos absurdos de spam)
            # 10 menções = Score 4.3 | 50 menções = Score 6.6 | 100 menções = Score 7.6
            score = min(1.0 + np.log(count + 1) * 1.5, 9.9)

            # Tenta buscar preço
            price_data = self.fetch_price(winner)
            
            if price_data:
                # É UM TICKER (Tem Preço)
                current_price = price_data[0]
                old_price = price_data[1]
                pct_change = (current_price - old_price) / old_price
                
                # Lag: Muito Hype (Score > 6) e Preço Parado (< 0.3%)
                is_lag = score > 6.0 and abs(pct_change) < 0.003
                display_type = "TICKER"
            else:
                # É UMA NARRATIVA (Sem Preço)
                pct_change = 0.0
                is_lag = False # Narrativas abstratas não têm "Lag de preço" direto
                display_type = "NARRATIVA"

            print(f"🔥 {display_type}: {winner} (Score: {score:.1f})")
            print(f"   🗣️ Evidência: \"{evidence[:50]}...\"")

            if self.db:
                self.db.save_signal(
                    symbol=winner, 
                    score=score,
                    price_change=pct_change,
                    is_lag=is_lag,
                    top_mentions=top_dict,
                    evidence_text=evidence
                )
                
        except Exception as e:
            print(f"❌ ERRO GERAL: {e}")

if __name__ == "__main__":
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()
    
    app = MoltbookApp()
    while True:
        app.run()
        print("🏁 Ciclo concluído. Dormindo 1h...")
        time.sleep(3600)