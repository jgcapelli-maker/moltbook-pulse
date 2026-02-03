import json
import nltk
import os
from nltk.sentiment.vader import SentimentIntensityAnalyzer

class MoltPulseEngine:
    def __init__(self, lexicon_path=None):
        # ... (código anterior de path mantido) ...
        if lexicon_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            lexicon_path = os.path.join(base_dir, 'config', 'lexicon.json')
            
        nltk.download('vader_lexicon', quiet=True)
        self.sia = SentimentIntensityAnalyzer()
        
        try:
            # AQUI ESTÁ A CORREÇÃO: encoding='utf-8-sig'
            with open(lexicon_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                self.sia.lexicon.update(data['lexicon'])
                print(f"DEBUG: Lexicon customizado carregado com sucesso! ({len(data['lexicon'])} termos)")
        except Exception as e:
            print(f"ERRO CRÍTICO ao carregar Lexicon: {e}")
            # Fallback
            self.sia.lexicon.update({"moon": 4.0, "rekt": -4.0}) 

    def analyze(self, texts):
        if not texts: return 0.1 
        scores = [self.sia.polarity_scores(t)['compound'] for t in texts]
        return sum(scores) / len(scores)