import os

# --- COLE SUAS CHAVES AQUI DENTRO DAS ASPAS ---
SUPABASE_URL = "https://lujwyxmvpxajgndonpfn.supabase.co"
SUPABASE_KEY = "sb_publishable_vHJzSQnJoQjpjsEJGuUgvw_NMlQkg8E"
# ----------------------------------------------

# Caminho para a raiz do projeto (onde o .env deve ficar)
# Sobe um nível a partir da pasta 'src'
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_file = os.path.join(root_path, '.env')

print(f"Escrevendo configurações em: {env_file}")

content = f"SUPABASE_URL={SUPABASE_URL}\nSUPABASE_KEY={SUPABASE_KEY}"

try:
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCESSO: Arquivo .env recriado com encoding UTF-8 limpo.")
    print("Verifique se as chaves acima estão corretas.")
except Exception as e:
    print(f"ERRO ao escrever arquivo: {e}")