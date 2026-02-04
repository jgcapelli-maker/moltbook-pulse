import os
from dotenv import load_dotenv
from supabase import create_client

# 1. Carrega as chaves
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"🔑 URL encontrada: {url[:20]}...")
print(f"🔑 KEY encontrada: {key[:20]}...")

if not url or not key:
    print("❌ ERRO: Faltam variáveis no arquivo .env")
    exit()

# 2. Conecta
try:
    supabase = create_client(url, key)
    print("✅ Conexão inicial OK.")
except Exception as e:
    print(f"❌ Falha ao criar cliente: {e}")
    exit()

# 3. Tenta Inserir (Debug Mode)
print("⏳ Tentando inserir dado de teste...")
try:
    data = {
        "symbol": "TEST-DB",
        "sentiment_score": 9.9,
        "price_change": 0.0,
        "is_lag": False
    }
    
    # Executa e pede para retornar o dado inserido (count='exact' força resposta)
    response = supabase.table("market_pulse").insert(data).execute()
    
    print("🔍 RESPOSTA DO SUPABASE:")
    print(response)
    
    if response.data:
        print("🎉 SUCESSO! O dado foi gravado e retornado.")
    else:
        print("⚠️ ALERTA: O comando rodou, mas nenhum dado voltou. Provável bloqueio de RLS.")

except Exception as e:
    print("❌ ERRO CRÍTICO NA INSERÇÃO:")
    print(e)
    print("-" * 30)
    print("DICA: Verifique se o nome das colunas na tabela é igual ao do código.")