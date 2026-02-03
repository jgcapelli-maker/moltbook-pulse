import pandas as pd
from engine.pulse_engine import MoltPulseEngine
from database import MoltDatabase
from engine.hive_scraper import HiveScraper # <--- O NOVO MOTOR
import requests
import matplotlib.pyplot as plt
import os
from datetime import datetime

class MoltbookApp:
    def __init__(self):
        self.engine = MoltPulseEngine()
        self.db = MoltDatabase() 
        self.hive = HiveScraper()

    def fetch_price(self, symbol):
        # Limpa o ticker (ex: $PEPE -> PEPEUSDT)
        clean_symbol = symbol.replace('$', '') + "USDT"
        print(f"📉 CHECK: Buscando preço para {clean_symbol}...")
        
        url = "https://api.binance.com/api/v3/klines"
        params = {'symbol': clean_symbol, 'interval': '1m', 'limit': 60}
        
        try:
            r = requests.get(url, params=params, timeout=5)
            data = r.json()
            
            if isinstance(data, dict) and 'code' in data:
                print(f"   ⚠️ Token {clean_symbol} não listado na Binance ou erro API.")
                return None

            df = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'vol', 'ct', 'qa', 'n', 'tb', 'tqa', 'i'])
            df['ts'] = pd.to_datetime(df['ts'], unit='ms')
            df['close'] = df['close'].astype(float)
            return df
        except:
            return None

    def run(self):
        print("--- INICIANDO ESCUTA DA COLMEIA (MOLTBOOK.COM) ---")
        
        # 1. Descobrir Tickers Quentes
        trending_list = self.hive.scan_hive()
        
        if not trending_list:
            print("💤 Nenhum ticker detectado na conversa dos agentes.")
            return

        # Pega o Top 1 (O mais falado)
        top_gem = trending_list[0][0] # Ex: 'PEPE'
        mentions = trending_list[0][1]
        print(f"🔥 GEM DETECTADA: ${top_gem} com {mentions} menções.")

        # 2. Verificar Preço Real
        df = self.fetch_price(top_gem)
        
        if df is None:
            print(f"🚫 ${top_gem} é muito nova (ainda não está na Binance). Oportunidade DEX/On-chain!")
            # Aqui poderíamos integrar DexScreener no futuro
            return

        # 3. Gerar Visual
        # O "Sentimento" agora é baseado no VOLUME de menções (Hype)
        pulse_score = min(mentions * 0.5, 5.0) # Normaliza (10 menções = Score 5.0)
        
        price_change = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
        
        # Se falam muito (>3 menções) e o preço subiu pouco (<1%), é LAG
        is_lag = mentions >= 3 and abs(price_change) < 0.01
        
        # 4. Salvar
        if self.db:
            self.db.save_signal(f"${top_gem}", pulse_score, price_change, is_lag)
            
        self.generate_visual(df, top_gem, mentions, is_lag)
        print(f"🏁 RELATÓRIO: Agentes focados em ${top_gem}. Lag: {is_lag}")

    def generate_visual(self, df, symbol, mentions, is_lag):
        try:
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(10,5))
            
            ax.plot(df['ts'], df['close'], color='#00ffcc', linewidth=2)
            
            title_text = f"MOLTBOOK HIVE MIND: ${symbol}\nMentions: {mentions} (Viral) | Lag: {is_lag}"
            plt.title(title_text, color='white', fontweight='bold')
            
            # Anotação de Hype
            ax.annotate('AI AGENTS PUMPING', xy=(df['ts'].iloc[-1], df['close'].iloc[-1]), 
                         xytext=(df['ts'].iloc[-20], df['close'].iloc[-1]),
                         arrowprops=dict(facecolor='yellow', shrink=0.05),
                         color='yellow')

            output_path = os.path.join("data", "outputs", "latest_signal.png")
            plt.savefig(output_path)
            plt.close()
            print(f"📸 EVIDÊNCIA SALVA: {output_path}")
        except Exception as e:
            print(f"⚠️ ERRO VISUAL: {e}")

if __name__ == "__main__":
    app = MoltbookApp()
    app.run()