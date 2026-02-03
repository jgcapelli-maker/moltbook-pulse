import pandas as pd
from engine.pulse_engine import MoltPulseEngine
from database import MoltDatabase
from engine.hive_scraper import HiveScraper
import requests
import matplotlib.pyplot as plt
import os
import time
import numpy as np # Importante para dados sintéticos
from datetime import datetime, timedelta

class MoltbookApp:
    def __init__(self):
        self.engine = MoltPulseEngine()
        self.db = MoltDatabase() 
        self.hive = HiveScraper()

    def fetch_price(self, symbol):
        clean_symbol = symbol.replace('$', '') + "USDT"
        print(f"📉 CHECK: Buscando preço para {clean_symbol}...")
        
        # Lista de tentativas (EUA vs Mundo)
        urls = [
            "https://api.binance.us/api/v3/klines", # Tenta Binance US (Render fica nos EUA)
            "https://api.binance.com/api/v3/klines" # Tenta Global
        ]
        
        for url in urls:
            try:
                params = {'symbol': clean_symbol, 'interval': '1m', 'limit': 60}
                # Timeout curto para ser rápido
                r = requests.get(url, params=params, timeout=3)
                data = r.json()
                
                # Verifica erro da API
                if isinstance(data, dict) and ('code' in data or 'msg' in data):
                    continue # Tenta a próxima URL

                # Sucesso
                df = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'vol', 'ct', 'qa', 'n', 'tb', 'tqa', 'i'])
                df['ts'] = pd.to_datetime(df['ts'], unit='ms')
                df['close'] = df['close'].astype(float)
                return df
            except Exception as e:
                continue # Falha de conexão, tenta próxima
        
        # --- PLANO C: SIMULAÇÃO TOTAL (FAIL-SAFE) ---
        print("   ⚠️ APIs Bloqueadas (Geo-fence). Gerando dados sintéticos para completar o ciclo.")
        dates = [datetime.now() - timedelta(minutes=i) for i in range(60)]
        dates.reverse()
        # Cria um preço fictício de 100 subindo levemente
        prices = [100 + (i * 0.05) + np.random.normal(0, 0.2) for i in range(60)] 
        
        df_dummy = pd.DataFrame({'ts': dates, 'close': prices})
        return df_dummy

    def run(self):
        # Loop Infinito para manter o Render "Vivo"
        while True:
            print(f"\n--- CICLO INICIADO: {datetime.now()} ---")
            
            try:
                # 1. Escuta a Colmeia
                trending_list = self.hive.scan_hive()
                
                # Seleciona o alvo
                if trending_list:
                    top_gem = trending_list[0][0]
                    mentions = trending_list[0][1]
                else:
                    # Fallback de segurança se hive retornar vazio
                    top_gem = "BTC"
                    mentions = 5

                print(f"🔥 ALVO: ${top_gem} ({mentions} menções)")

                # 2. Preço (Com sistema Anti-Bloqueio)
                df = self.fetch_price(top_gem)
                
                # 3. Análise
                pulse_score = min(mentions * 0.5, 5.0)
                price_change = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
                is_lag = mentions >= 3 and abs(price_change) < 0.01
                
                # 4. Salvar
                if self.db:
                    self.db.save_signal(f"${top_gem}", pulse_score, price_change, is_lag)
                    
                self.generate_visual(df, top_gem, mentions, is_lag)
                print(f"🏁 CICLO CONCLUÍDO. Dormindo por 1 hora...")

            except Exception as e:
                print(f"❌ ERRO CRÍTICO NO LOOP: {e}")
            
            # Dorme 1 hora (3600 segundos) antes de rodar de novo
            # Isso impede o erro "Application exited early"
            time.sleep(3600) 

    def generate_visual(self, df, symbol, mentions, is_lag):
        try:
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(10,5))
            
            ax.plot(df['ts'], df['close'], color='#00ffcc', linewidth=2)
            
            title_text = f"MOLTBOOK HIVE MIND: ${symbol}\nMentions: {mentions} (Viral) | Lag: {is_lag}"
            plt.title(title_text, color='white', fontweight='bold')
            
            output_dir = os.path.join("data", "outputs")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "latest_signal.png")
            
            plt.savefig(output_path)
            plt.close()
            print(f"📸 CARD SALVO: {output_path}")
        except Exception as e:
            print(f"⚠️ ERRO VISUAL: {e}")

if __name__ == "__main__":
    app = MoltbookApp()
    app.run()