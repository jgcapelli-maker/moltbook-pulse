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
        # Configurações anti-crash para ambiente Serverless (Render/Heroku)
        chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222") # Ajuda a estabilizar
        # User-agent genérico e seguro
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        return webdriver.Chrome(options=chrome_options)

    def scan_hive(self):
        driver = self.setup_driver()
        print("   ⏳ Iniciando Mineração (Modo Seguro)...")
        
        try:
            driver.get(self.url)
            
            # Espera genérica pelo BODY (mais seguro que esperar 'article')
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # --- FASE 1: SCROLL ---
            for _ in range(5): 
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2) 
            
            # --- FASE 2: COLETA ---
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            # Pega qualquer texto relevante
            content_blocks = soup.find_all(['p', 'div', 'span', 'article'])
            
            fresh_comments = []
            discarded_count = 0
            full_fresh_text = ""
            
            # --- FASE 3: FILTRO (Time Gate) ---
            for block in content_blocks:
                text = block.get_text(" ", strip=True)
                
                # Descarta se tiver horas/dias/anos
                is_old = re.search(r'\d+\s*[hdy]\s*ago', text, re.IGNORECASE)
                
                if is_old:
                    discarded_count += 1
                    continue 
                
                if len(text) > 20 and text not in fresh_comments:
                    clean_text = " ".join(text.split())
                    fresh_comments.append(clean_text)
                    full_fresh_text += " " + clean_text

            print(f"   ✅ Amostra FRESCA: {len(fresh_comments)} itens. (Desc: {discarded_count})")

            # --- FASE 4: TICKERS ---
            pattern = r'\$([a-zA-Z]{2,6})'
            matches = re.findall(pattern, full_fresh_text)
            ignored = ['USDT', 'USD', 'USDC', 'DAI', 'BUSD']
            clean_matches = [m.upper() for m in matches if m.upper() not in ignored and len(m) > 1]
            
            counts = Counter(clean_matches)
            
            if not counts:
                print("   ⚠️ Nenhum ticker detectado.")
                return [], "Silêncio na rede recente", {}

            top_trends = counts.most_common(5)
            winner_symbol = top_trends[0][0]
            winner_count = top_trends[0][1]
            top_mentions_dict = {k: v for k, v in top_trends}

            # --- FASE 5: EVIDÊNCIA ---
            evidence = f"Menção a ${winner_symbol} detectada."
            for comment in reversed(fresh_comments): 
                if f"${winner_symbol}" in comment or winner_symbol in comment:
                    if 30 < len(comment) < 400: 
                        evidence = comment
                        break 

            print(f"   🏆 TENDÊNCIA: ${winner_symbol} ({winner_count} menções)")
            return top_trends, evidence, top_mentions_dict

        except Exception as e:
            print(f"   ❌ Erro no Scraper: {e}")
            return [], "Erro técnico", {}
        finally:
            driver.quit()