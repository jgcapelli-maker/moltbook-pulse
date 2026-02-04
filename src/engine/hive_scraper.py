from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
from collections import Counter

class HiveScraper:
    def __init__(self):
        self.url = "https://moltbook.com"
        
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # User-agent moderno para evitar bloqueios
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        return webdriver.Chrome(options=chrome_options)

    def scan_hive(self):
        driver = self.setup_driver()
        print("   ⏳ Iniciando Mineração com Filtro Temporal...")
        
        try:
            driver.get(self.url)
            
            # Espera o feed carregar
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # --- FASE 1: CARREGAMENTO DE CARGA (Scroll) ---
            # Rola 5 vezes para carregar um bom volume de posts (recentes e médio-recentes)
            for _ in range(5): 
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2.5) # Tempo para o AJAX carregar os novos posts no final
            
            # --- FASE 2: COLETA BRUTA ---
            print("   📰 Coletando HTML bruto da página inteira...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            # Foca em 'article' ou 'div' de conteúdo para pegar texto + timestamp juntos
            content_blocks = soup.find_all(['article', 'div'], class_=lambda x: x and 'post' in x.lower())
            if not content_blocks:
                 content_blocks = soup.find_all(['p', 'span', 'h1', 'h2', 'h3']) # Fallback

            
            fresh_comments = []
            discarded_count = 0
            full_fresh_text = ""
            
            # --- FASE 3: O GRANDE FILTRO (Time Gate) ---
            print(f"   🕵️ Analisando {len(content_blocks)} blocos de conteúdo...")
            for block in content_blocks:
                text = block.get_text(" ", strip=True) # Pega todo texto dentro do bloco
                
                # Regex: Procura dígitos seguidos de 'h' (horas), 'd' (dias) ou 'y' (anos) + 'ago'
                # Ex: "6h ago", "1d ago"
                is_old = re.search(r'\d+\s*[hdy]\s*ago', text, re.IGNORECASE)
                
                if is_old:
                    discarded_count += 1
                    continue # LIXO DETECTADO. Pula para o próximo.
                
                # Se passou pelo filtro, consideramos "fresco" (minutos, segundos ou sem data)
                if len(text) > 20 and text not in fresh_comments:
                    clean_text = " ".join(text.split())
                    fresh_comments.append(clean_text)
                    full_fresh_text += " " + clean_text

            print(f"   ✅ Amostra FRESCA final: {len(fresh_comments)} fragmentos.")
            print(f"   🗑️ Lixo descartado (antigo): {discarded_count} itens.")

            # --- FASE 4: MINERAÇÃO DE TICKERS (Regex Universal) ---
            # Busca padrão $TICKER (2 a 6 letras maiúsculas/minúsculas)
            pattern = r'\$([a-zA-Z]{2,6})'
            matches = re.findall(pattern, full_fresh_text)
            
            # Limpeza (Remove stablecoins e ruído comum)
            ignored_tickers = ['USDT', 'USD', 'USDC', 'DAI', 'BUSD', 'crypto', 'token']
            clean_matches = [m.upper() for m in matches if m.upper() not in ignored_tickers and len(m) > 1]
            
            counts = Counter(clean_matches)
            
            if not counts:
                print("   ⚠️ Nenhum ticker válido detectado na amostra fresca.")
                return [], "Silêncio na rede recente", {}

            # Pega o Top 5 para estatística
            top_trends = counts.most_common(5)
            winner_symbol = top_trends[0][0]
            winner_count = top_trends[0][1]
            
            # Prepara o dicionário para o JSONB do banco
            top_mentions_dict = {k: v for k, v in top_trends}

            # --- FASE 5: BUSCA DE EVIDÊNCIA ---
            # Procura a melhor frase de exemplo dentro dos comentários FRESCOS
            evidence = f"Menção a ${winner_symbol} detectada."
            # Varre de trás pra frente (reversed) para tentar pegar os mais recentes do fundo da página primeiro
            for comment in reversed(fresh_comments): 
                if f"${winner_symbol}" in comment or winner_symbol in comment:
                    # Prioriza comentários com tamanho médio (mais chance de ter conteúdo real)
                    if 50 < len(comment) < 300: 
                        evidence = comment
                        break # Achou uma boa, para de procurar

            print(f"   🏆 TENDÊNCIA (FRESH): ${winner_symbol} ({winner_count} menções)")
            return top_trends, evidence, top_mentions_dict

        except Exception as e:
            print(f"   ❌ Erro no Scraper: {e}")
            return [], "Erro na leitura", {}
        finally:
            driver.quit()