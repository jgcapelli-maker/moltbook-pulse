import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# FORÇA A BUSCA DO ARQUIVO .ENV NA RAIZ DO PROJETO
# Pega o caminho deste arquivo (database.py), sobe duas pastas e procura o .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class MoltDatabase:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        self.client = None
        
        print(f"DEBUG: Procurando .env em: {env_path}")
        
        if url and key:
            try:
                self.client: Client = create_client(url, key)
                print("DEBUG: Conexão com Supabase iniciada (Credenciais carregadas).")
            except Exception as e:
                print(f"ERRO Supabase Connection: {e}")
        else:
            print("AVISO: Credenciais .env AINDA não encontradas. Verifique se o arquivo existe em 'MoltP1/.env'")

    def save_signal(self, ticker, pulse, price_change, is_lag):
        if not self.client: 
            print("DB SKIP: Modo Offline (sem cliente).")
            return
        
        data = {
            "ticker": ticker,
            "pulse_score": float(pulse),
            "price_change_pct": float(price_change),
            "is_lag": bool(is_lag),
            "raw_sentiment_data": "Automated Scan"
        }
        
        try:
            self.client.table("signals").insert(data).execute()
            print(f"SUCCESS: Sinal salvo no DB para {ticker}!")
        except Exception as e:
            print(f"ERRO ao salvar no DB: {e}")