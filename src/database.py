import os
from supabase import create_client
from dotenv import load_dotenv

class MoltDatabase:
    def __init__(self):
        load_dotenv()
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            print("⚠️ AVISO: Credenciais do Supabase não encontradas!")
            self.client = None
        else:
            try:
                self.client = create_client(url, key)
                print("DEBUG: Conexão com Supabase iniciada (Credenciais carregadas).")
            except Exception as e:
                print(f"❌ Erro ao conectar Supabase: {e}")
                self.client = None

    def save_signal(self, symbol, score, price_change, is_lag, top_mentions=None, evidence_text=None):
        if not self.client:
            print("❌ Erro: Banco de dados desconectado. Não foi possível salvar.")
            return

        try:
            # Prepara o pacote de dados
            data = {
                "symbol": symbol,
                "sentiment_score": float(score),
                "price_change": float(price_change),
                "is_lag": bool(is_lag),
                # Se não tiver dados novos, envia valores padrão para não quebrar
                "top_mentions": top_mentions if top_mentions else {},
                "evidence_text": evidence_text if evidence_text else "Sem evidência capturada."
            }
            
            self.client.table("market_pulse").insert(data).execute()
            print(f"   💾 SINAL SALVO COM SUCESSO PARA {symbol}!")
            
        except Exception as e:
            print(f"❌ ERRO AO SALVAR NO BANCO: {e}")