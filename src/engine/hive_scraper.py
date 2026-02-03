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
        
        # --- O INTERRUPTOR INTELIGENTE (TERRA vs NUVEM) ---
        # Se existir uma variável chamada 'RENDER', estamos na nuvem.
        if os.environ.get('RENDER'):
            print("☁️ MODO NUVEM DETECTADO: Usando Chrome Headless...")
            self.options.add_argument("--headless=new") 
            # Caminho onde o script .sh instalou o Chrome no Render
            self.options.binary_location = "/opt/render/project/.render/chrome/opt/google/chrome/chrome"
        else:
            # Estamos no seu PC (Windows)
            print("🖥️ MODO LOCAL: Usando Perfil Persistente...")
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            profile_path = os.path.join(base_dir, "chrome_profile")
            self.options.add_argument(f"--user-data-dir={profile_path}")

        # Lista de Alvos
        self.TARGETS = {
            'SOL': ['SOLANA', 'SOL'],
            'BTC': ['BITCOIN', 'BTC'],
            'ETH': ['ETHEREUM', 'ETH'],
            'DOGE': ['DOGECOIN', 'DOGE'],
            'PEPE': ['PEPE'],
            'WIF': ['WIF', 'DOGWIFHAT'],
            'TRUMP': ['TRUMP', 'MAGA'],
            'XRP': ['RIPPLE', 'XRP']
        }

    def scan_hive(self):
        print("🤖 HIVE: Conectando ao Moltbook.com...")
        
        driver = None
        posts_text = []
        
        try:
            # version_main=144 é importante para estabilidade
            driver = uc.Chrome(options=self.options, use_subprocess=True, version_main=144)
            url = "https://www.moltbook.com/" 
            driver.get(url)
            
            print("   ⏳ Lendo a mente da colmeia...")
            time.sleep(5) 
            
            # Scroll para pegar dados
            for i in range(5):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            elements = driver.find_elements(By.TAG_NAME, "p")
            elements += driver.find_elements(By.TAG_NAME, "span")
            
            for el in elements:
                try:
                    text = el.text.strip()
                    if len(text) > 10: 
                        posts_text.append(text)
                except: continue
                
            print(f"   ✅ Leitura concluída: {len(posts_text)} fragmentos capturados.")
            
        except Exception as e:
            print(f"❌ HIVE ERROR: {e}")
            
        finally:
            if driver:
                try: driver.quit()
                except: pass
        
        return self.extract_tickers(posts_text)

    def extract_tickers(self, texts):
        print("   🔍 Analisando dados...")
        found_tickers = []
        
        for text in texts:
            upper_text = text.upper()
            
            # 1. Regex ($XYZ)
            regex = r'\$([a-zA-Z]{3,6})'
            matches = re.findall(regex, text)
            for match in matches:
                ticker = match.upper()
                if ticker not in ['THE', 'AND', 'FOR']: 
                    found_tickers.append(ticker)

            # 2. Palavras-Chave
            for ticker, keywords in self.TARGETS.items():
                for kw in keywords:
                    if f" {kw} " in f" {upper_text} ":
                        found_tickers.append(ticker)
        
        counts = Counter(found_tickers)
        ranking = counts.most_common(5)
        
        if not ranking:
            print("   ⚠️ HIVE SILENCIOSA. Ativando Simulação BTC.")
            return [('BTC', 10), ('SOL', 5)] 
            
        print(f"   🏆 TENDÊNCIAS: {ranking}")
        return ranking