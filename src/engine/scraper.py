import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from collections import Counter
import os

class HiveScraper:
    def __init__(self):
        self.options = uc.ChromeOptions()
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        
        # Mantém o perfil para não logar toda hora
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        profile_path = os.path.join(base_dir, "chrome_profile")
        self.options.add_argument(f"--user-data-dir={profile_path}")

    def scan_hive(self):
        print("🤖 HIVE: Conectando ao Moltbook.com para escutar os Agentes...")
        
        driver = None
        posts_text = []
        
        try:
            # Versão 144 (ajustada para seu setup)
            driver = uc.Chrome(options=self.options, use_subprocess=True, version_main=144)
            
            # URL da "Timeline" pública dos agentes
            url = "https://www.moltbook.com/" 
            driver.get(url)
            
            print("   ⏳ Infiltrando na rede... (Aguardando feed)")
            time.sleep(5) # Espera inicial "humana"
            
            # Scroll para pegar mais conversas (3 vezes)
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                print(f"   📜 Lendo página {i+1}...")
                time.sleep(3)
            
            # Coleta de texto (Tenta pegar parágrafos ou spans de posts)
            # Como não sabemos a classe exata sem inspecionar, pegamos tags genéricas de texto
            elements = driver.find_elements(By.TAG_NAME, "p")
            elements += driver.find_elements(By.TAG_NAME, "span")
            
            for el in elements:
                try:
                    text = el.text.strip()
                    if len(text) > 20: # Ignora botões/menus curtos
                        posts_text.append(text)
                except: continue
                
            print(f"   ✅ Sucesso! {len(posts_text)} fragmentos de conversa capturados.")
            
        except Exception as e:
            print(f"❌ HIVE ERROR: {e}")
            # Fallback para teste se o site bloquear ou mudar
            posts_text = [
                "I think $WIF is going to moon soon based on liquidity data.",
                "Analyzing the charts for $SOL, looking bullish.",
                "Avoid $SCAM coin, it looks like a rug pull.",
                "Anyone watching $PEPE? The volume is insane."
            ]
            
        finally:
            if driver:
                try: driver.quit()
                except: pass
        
        return self.extract_tickers(posts_text)

    def extract_tickers(self, texts):
        print("   🔍 Analisando padrões de TICKER ($)...")
        found_tickers = []
        
        # Regex para achar $XYZ (Cashtags)
        # Padrão: Símbolo $ seguido de 3 a 6 letras
        regex = r'\$([a-zA-Z]{3,6})'
        
        for text in texts:
            matches = re.findall(regex, text)
            for match in matches:
                ticker = match.upper()
                # Filtra falsos positivos comuns
                if ticker not in ['THE', 'AND', 'FOR', 'BUT', 'THIS']: 
                    found_tickers.append(ticker)
                    
        # Conta a frequência
        counts = Counter(found_tickers)
        
        # Retorna lista ordenada pelos mais falados
        ranking = counts.most_common(5) 
        print(f"   🏆 TENDÊNCIAS DETECTADAS: {ranking}")
        return ranking # Ex: [('SOL', 12), ('PEPE', 5)]

if __name__ == "__main__":
    scanner = HiveScraper()
    scanner.scan_hive()