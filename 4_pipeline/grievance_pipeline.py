import sys
import os

# Add paths to all agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '3_agents', 'classification_agent')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '3_agents', 'sentiment_agent')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '3_agents', 'urgency_agent')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '3_agents', 'decision_agent')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '3_agents', 'translation_agent')))

# Import Agents
try:
    from classifier import ClassificationAgent
    from sentiment import SentimentAgent # Corrected from sentiment_analysis
    from urgency_detect import UrgencyAgent
    from decision import DecisionAgent # Corrected from decision_logic
    from translator import TranslationAgent
except ImportError as e:
    print(f"⚠️ Pipeline Import Error: {e}")

class GrievanceOrchestrator:
    def __init__(self):
        print("🤖 Initializing AI Pipeline...")
        self.translator = TranslationAgent()
        self.classifier = ClassificationAgent()
        self.sentiment = SentimentAgent()
        self.urgency = UrgencyAgent()
        self.decision = DecisionAgent()
        print("✅ Pipeline Ready.")

    def run_pipeline(self, text):
        # 1. TRANSLATE (The New Step)
        # We auto-detect and convert to English for the AI
        trans_res = self.translator.translate(text)
        english_text = trans_res['translated_text']
        
        # 2. CLASSIFY (Using English Text)
        cat_res = self.classifier.predict(english_text)
        
        # 3. SENTIMENT & URGENCY (Using English Text)
        sent_res = self.sentiment.analyze(english_text)
        urg_res = self.urgency.analyze_urgency(english_text)

        # 4. DECISION
        final = self.decision.compute_priority( # Corrected from calculate_priority based on decision.py
            category=cat_res['category'],
            sentiment_score=sent_res['score'],
            is_urgent=urg_res['is_urgent']
        )

        # 5. MERGE RESULTS
        return {
            "original_text": trans_res['original_text'],
            "translated_text": english_text,
            "is_translated": trans_res['is_translated'],
            "src_lang": trans_res['src_lang'],
            
            "category": cat_res['category'],
            "confidence": cat_res['confidence'],
            "sentiment_score": sent_res['score'],
            "is_urgent": urg_res['is_urgent'],
            "priority": final['priority'],
            "cci": final['cci']
        }
