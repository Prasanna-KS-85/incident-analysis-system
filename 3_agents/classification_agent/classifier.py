import os
import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

class ClassificationAgent:
    def __init__(self):
        # Path to the 'bert_brain' folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, 'bert_brain')
        
        self.model = None
        self.tokenizer = None

        # Load BERT
        try:
            print(f"🔄 Loading BERT model from: {model_path}...")
            self.tokenizer = DistilBertTokenizerFast.from_pretrained(model_path)
            self.model = DistilBertForSequenceClassification.from_pretrained(model_path)
            self.model.eval() # Set to evaluation mode (faster)
            print("✅ BERT Model Loaded Successfully!")
        except Exception as e:
            print(f"⚠️ CRITICAL ERROR: Could not load BERT model. Check if 'bert_brain' folder exists. Details: {e}")

    def predict(self, text):
        """
        Predicts category using the Fine-Tuned DistilBERT model.
        """
        # Fallback if model failed to load
        if not self.model or not self.tokenizer:
            return {"category": "System Error", "confidence": 0.0}

        try:
            # 1. Prepare Text (Tokenize)
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                padding=True, 
                max_length=128
            )
            
            # 2. Predict (Forward Pass)
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # 3. Convert Logits to Probabilities
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # 4. Get the Winner
            confidence, predicted_id = torch.max(probs, dim=-1)
            predicted_index = predicted_id.item()
            
            # 5. Get Label Name (The model remembers the label names from training!)
            category = self.model.config.id2label[predicted_index]
            
            return {
                "category": category,
                "confidence": round(confidence.item(), 2)
            }

        except Exception as e:
            print(f"Prediction Error: {e}")
            return {"category": "Error", "confidence": 0.0}
