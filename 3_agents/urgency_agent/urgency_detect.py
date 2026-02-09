import re

class UrgencyAgent:
    def __init__(self):
        # High-risk keywords that usually trigger an alert
        self.urgent_keywords = [
            "fire", "explosion", "gas leak", "sparking", "collapse", 
            "accident", "bleeding", "electrocution", "flood", "live wire",
            "burning", "smell of gas", "short circuit"
        ]
        
        # Phrases that cancel out the urgency (Negations)
        self.negation_patterns = [
            r"no\s+fire",           # "no fire"
            r"not\s+a\s+fire",      # "not a fire"
            r"false\s+alarm",       # "false alarm"
            r"drill",               # "fire drill"
            r"testing",             # "testing the alarm"
            r"controlled",          # "controlled burning"
            r"just\s+smoke",        # "just smoke"
            r"bbq",                 # "bbq"
            r"cooking",             # "cooking"
        ]

    def analyze_urgency(self, text):
        """
        Determines if a complaint is urgent based on keywords, 
        but acts smart by checking for negations first.
        """
        text_lower = text.lower()
        
        # 1. Check for Negations (The "Safety Check")
        # If the text contains "no fire" or "bbq", we ignore the urgency.
        for pattern in self.negation_patterns:
            if re.search(pattern, text_lower):
                return {"is_urgent": False, "reason": f"Negated by '{pattern}'"}

        # 2. Check for Urgent Keywords
        matched_keywords = [word for word in self.urgent_keywords if word in text_lower]
        
        if matched_keywords:
            return {
                "is_urgent": True, 
                "keywords": matched_keywords,
                "reason": "Found critical keywords"
            }
        
        return {"is_urgent": False, "reason": "No critical keywords found"}
