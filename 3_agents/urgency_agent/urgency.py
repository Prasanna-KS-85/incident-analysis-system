class UrgencyAgent:
    def __init__(self):
        # Define a list of critical keywords
        self.urgency_keywords = [
            "danger", "emergency", "accident", "collapse", 
            "leak", "fire", "explosion", "injury", "fatal",
            "trapped", "hazard", "spark", "flood"
        ]

    def check_urgency(self, text):
        """
        Scans the text for urgency keywords.
        Returns True if any keyword is found.
        """
        text_lower = text.lower()
        found_keywords = [word for word in self.urgency_keywords if word in text_lower]
        
        return {
            "is_urgent": len(found_keywords) > 0,
            "keywords": found_keywords,
            "score": 1.0 if len(found_keywords) > 0 else 0.0
        }
