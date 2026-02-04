from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
from collections import Counter
import logging

# Configuração de Log limpo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HiveScraper:
    def __init__(self):
        self.url = "https://moltbook.com"
        
        # STOPWORDS: Lista robusta para limpeza de ruído
        # Removemos verbos, preposições e gírias genéricas que não indicam narrativa
        self.STOPWORDS = set([
            "the", "and", "is", "in", "it", "to", "of", "for", "on", "that", "this", "with", "are", 
            "you", "was", "be", "at", "as", "have", "not", "but", "can", "will", "just", "if", "or", 
            "what", "so", "me", "my", "all", "up", "out", "do", "get", "no", "we", "like", "when", 
            "from", "has", "how", "go", "one", "they", "crypto", "market", "price", "chart", "pump", 
            "dump", "buy", "sell", "holding", "bag", "moon", "bullish", "bearish", "gem", "coins", 
            "token", "project", "community", "team", "good", "great", "best", "check", "guys", 
            "today", "now", "time", "week", "year", "day", "hour", "minutes", "ago", "reply", 
            "posted", "share", "report", "hide", "save", "comments", "submolts", "view", "more", 
            "loading", "show", "read", "people", "think", "know", "see", "going", "make", "money",
            "search", "notifications", "profile", "home", "explore", "messages"
        ])

    def setup_driver(self):
        """Configura o Chrome para ambiente Serverless (Low Memory/CPU)"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new") # Modo headless moderno
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage") # Usa /tmp em vez de /dev/shm
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        # Bloqueia imagens para economizar banda e RAM
        chrome_options.add_argument("--blink-settings=imagesEnabled=false") 
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        return webdriver.Chrome(options=chrome_options)

    def _generate_ngrams(self, text, n):
        """Gera N-grams (sequências de N palavras) a partir de um texto."""
        words = [w for w in re.findall(r'\b[a-zA-Z0-9$]+\b', text.lower()) if w not in self.STOPWORDS and len(w) > 2]
        return [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]

    def scan_hive(self):
        driver = None
        try:
            driver = self.setup_driver()
            print("   ⏳ [NLP ENGINE] Iniciando Varredura Neural da Colmeia...")
            
            driver.set_page_load_timeout(30)
            driver.get(self.url)
            
            # Wait inteligente pelo container principal
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # --- FASE 1: SMART SCROLL BUFFER ---
            # Coleta dados progressivamente sem estourar memória
            # Rola 6 vezes (aprox. 120-150 posts)
            for i in range(6): 
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5 + (i * 0.2)) # Espera progressiva para simular humano e dar tempo ao AJAX
            
            # --- FASE 2: EXTRAÇÃO E FILTRAGEM TEMPORAL ---
            # Usamos BS4 porque é 10x mais rápido que Selenium para parsear texto
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Seleciona blocos de texto genéricos (article, div de post, p)
            content_blocks = soup.find_all(['p', 'div', 'span', 'article', 'h1', 'h2'])
            
            fresh_sentences = []
            discarded_old = 0
            
            # Regex Cirúrgico: Detecta dígitos + h/d/y (ex: "2h ago", "1d", "3 y ago")
            time_filter_regex = re.compile(r'\b\d+\s*(h|d|y|hr|day|yr)s?\b', re.IGNORECASE)
            
            for block in content_blocks:
                text = block.get_text(" ", strip=True)
                
                # 1. Filtro Temporal
                if time_filter_regex.search(text):
                    discarded_old += 1
                    continue
                
                # 2. Filtro de Qualidade Mínima
                # Ignora textos muito curtos (bot spam) ou muito longos (copy-paste de artigo)
                if 20 < len(text) < 500:
                    fresh_sentences.append(text)

            print(f"   ✅ Buffer Processado: {len(fresh_sentences)} fragmentos recentes (Descartados: {discarded_old})")

            if not fresh_sentences:
                return [], "Silêncio absoluto na rede recente.", {}

            # --- FASE 3: DETECÇÃO DE NARRATIVAS (NLP N-GRAMS) ---
            all_ngrams = []
            
            for sentence in fresh_sentences:
                # Prioridade 1: Tickers explícitos ($BTC, $AI)
                tickers = re.findall(r'\$[A-Za-z]{2,6}', sentence.upper())
                all_ngrams.extend(tickers * 3) # Peso triplo para tickers explícitos
                
                # Prioridade 2: Bigrams (Ex: "AI AGENTS", "RWA TOKEN") - Onde mora o valor
                bigrams = self._generate_ngrams(sentence, 2)
                all_ngrams.extend([b.upper() for b in bigrams])
                
                # Prioridade 3: Unigrams (Palavras-chave fortes isoladas)
                unigrams = self._generate_ngrams(sentence, 1)
                all_ngrams.extend([u.upper() for u in unigrams])

            # Contagem de Frequência
            counts = Counter(all_ngrams)
            
            # Remove falsos positivos (termos que aparecem só 1 vez são ruído)
            counts = {k: v for k, v in counts.items() if v > 1}
            
            if not counts:
                # Fallback se tudo for ruído único
                return [], "Dispersão de tópicos. Sem consenso.", {}

            # Ordena pelo Top 5
            sorted_trends = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
            top_winner = sorted_trends[0][0] # Ex: "AI AGENTS"
            top_count = sorted_trends[0][1]
            top_dict = dict(sorted_trends)

            # --- FASE 4: EXTRAÇÃO DE EVIDÊNCIA CONTEXTUAL ---
            # Busca a melhor frase original que contém o vencedor
            best_evidence = "Tendência identificada via análise de frequência."
            winner_clean = top_winner.replace("$", "").lower()
            
            candidates = []
            for sentence in fresh_sentences:
                if winner_clean in sentence.lower():
                    candidates.append(sentence)
            
            # Escolhe a frase de tamanho médio (geralmente a mais explicativa)
            if candidates:
                # Ordena por proximidade do tamanho ideal (100 caracteres)
                candidates.sort(key=lambda s: abs(len(s) - 100))
                best_evidence = candidates[0]

            print(f"   🏆 NARRATIVA DOMINANTE: {top_winner} ({top_count} ocorrências)")
            print(f"   🗣️ CONTEXTO: \"{best_evidence[:60]}...\"")
            
            return sorted_trends, best_evidence, top_dict

        except Exception as e:
            print(f"   ❌ Erro Crítico no Scraper SOTA: {e}")
            return [], f"Erro de processamento: {str(e)[:50]}", {}
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass