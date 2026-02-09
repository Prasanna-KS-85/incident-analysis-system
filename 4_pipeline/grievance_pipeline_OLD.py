import sys
import os

# Add the project root to sys.path to allow imports from sibling directories
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fix import paths since we are running this as a script and also as a module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import importlib.util

def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Paths to agents
agents_dir = os.path.join(parent_dir, "3_agents")
classifier_path = os.path.join(agents_dir, "classification_agent", "classifier.py")
sentiment_path = os.path.join(agents_dir, "sentiment_agent", "sentiment.py")
urgency_path = os.path.join(agents_dir, "urgency_agent", "urgency_detect.py")
decision_path = os.path.join(agents_dir, "decision_agent", "decision.py")

# Import agents
ClassificationAgent = import_module_from_path("classifier", classifier_path).ClassificationAgent
SentimentAgent = import_module_from_path("sentiment", sentiment_path).SentimentAgent
UrgencyAgent = import_module_from_path("urgency_detect", urgency_path).UrgencyAgent
DecisionAgent = import_module_from_path("decision", decision_path).DecisionAgent


class GrievanceOrchestrator:
    def __init__(self):
        self.classifier = ClassificationAgent()
        self.sentiment_analyzer = SentimentAgent()
        self.urgency_detector = UrgencyAgent()
        self.decision_maker = DecisionAgent()

    def run_pipeline(self, text):
        print(f"Processing Text: {text}")
        
        # 1. Classification
        classification_result = self.classifier.predict(text)
        print(f"Classification: {classification_result}")
        
        # 2. Sentiment
        sentiment_result = self.sentiment_analyzer.analyze(text)
        print(f"Sentiment: {sentiment_result}")
        
        # 3. Urgency
        urgency_result = self.urgency_detector.analyze_urgency(text)
        print(f"Urgency: {urgency_result}")
        
        # 4. Decision
        decision_result = self.decision_maker.compute_priority(
            classification_result["category"],
            sentiment_result["score"],
            urgency_result["is_urgent"]
        )
        print(f"Decision: {decision_result}")
        
        return {
            "text": text,
            "classification": classification_result,
            "sentiment": sentiment_result,
            "urgency": urgency_result,
            "decision": decision_result
        }

if __name__ == "__main__":
    orchestrator = GrievanceOrchestrator()
    test_text = "There is a huge gas leak in the main street!"
    result = orchestrator.run_pipeline(test_text)
    print("\n--- FINAL OUTPUT ---")
    print(result)
