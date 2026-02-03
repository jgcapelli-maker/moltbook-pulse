import requests
import xml.etree.ElementTree as ET

class PulseFeedReader:
    def __init__(self):
        # Headers simples são suficientes para RSS do Google
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; MoltbookPulse/1.0; +http://moltbook.com)'
        }

    def get_headlines(self, coin_symbol):
        # Mapeamento para garantir busca correta
        query = f"{coin_symbol} crypto"
        if coin_symbol.lower() == 'sol': query = "solana crypto"
        if coin_symbol.lower() == 'btc': query = "bitcoin crypto"
        if coin_symbol.lower() == 'eth': query = "ethereum crypto"

        print(f"📡 FEED: Conectando ao Google News RSS para '{query}'...")
        
        # URL Mágica do Google News RSS
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        headlines = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                # Parse do XML
                root = ET.fromstring(response.content)
                
                # O RSS do Google estrutura as notícias dentro de <item> -> <title>
                for item in root.findall('.//item'):
                    title = item.find('title').text
                    # Limpeza básica (Remove o nome do jornal no final, ex: "... - CoinDesk")
                    clean_title = title.split(' - ')[0]
                    headlines.append(clean_title)
                    
                    # Limite para não sobrecarregar o VADER
                    if len(headlines) >= 15:
                        break
                
                print(f"   ✅ Sucesso! {len(headlines)} manchetes baixadas via RSS.")
            else:
                print(f"   ❌ Erro HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ FEED ERRO: {e}")
            
        # Fallback se o Google falhar (raro)
        if not headlines:
            print("   ⚠️ AVISO: Feed vazio. Retornando dados neutros.")
            return ["Market is monitoring the price action", "Waiting for volume"]
            
        return headlines

if __name__ == "__main__":
    reader = PulseFeedReader()
    news = reader.get_headlines("SOL")
    for n in news[:3]: print(f"- {n}")