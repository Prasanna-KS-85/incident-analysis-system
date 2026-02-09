class DecisionAgent:
    def __init__(self):
        # Base scores for different categories
        self.category_weights = {
            "Public Safety & Emergency": 8.0,      # Increased from default
            "Fire & Disaster": 9.0,                # Critical
            "Electrical & Power Infrastructure": 7.0,
            "Medical & Health": 8.0,
            "Water Supply & Drainage": 6.0,
            "Roads & Transportation Infrastructure": 5.0,
            "Sanitation & Public Health": 5.0,
            "Traffic & Civic Discipline": 4.0,
            "Noise & Environmental Issues": 3.0,
            "Animal-Related Issues": 3.0,
            "Urban Facilities & Amenities": 3.0
        }

    def compute_priority(self, category, sentiment_score, is_urgent):
        """
        Calculates the Civil Criticality Index (CCI) from 0 to 10.
        """
        # 1. Base Score from Category (Default to 4.0 if unknown)
        base_score = self.category_weights.get(category, 4.0)
        
        # 2. Urgency Booster
        # If Urgent, we add specific bonuses based on context
        urgency_bonus = 0.0
        if is_urgent:
            if base_score >= 7.0:
                urgency_bonus = 2.0  # Massive boost for already dangerous categories
            else:
                urgency_bonus = 1.5  # Standard boost for others

        # 3. Sentiment Adjuster
        # Negative sentiment (-0.9) adds urgency (+0.9). Positive sentiment reduces it.
        # We invert the score: More negative = Higher Risk
        sentiment_impact = abs(sentiment_score) * 1.5 if sentiment_score < 0 else 0

        # 4. Final Calculation
        final_score = base_score + urgency_bonus + sentiment_impact
        
        # 5. Cap the score at 10.0
        final_score = min(round(final_score, 1), 10.0)

        # 6. Determine Priority Label
        if final_score >= 7.5:
            priority = "High"
        elif final_score >= 4.5:
            priority = "Medium"
        else:
            priority = "Low"

        return {
            "priority": priority,
            "cci": final_score
        }
