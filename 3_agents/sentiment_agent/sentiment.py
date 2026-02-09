from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

class SentimentAgent:
    def __init__(self):
        # Download the lexicon if not present
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon')
            
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze(self, text):
        """
        Returns a sentiment score between -1.0 (Negative) and +1.0 (Positive).
        """
        scores = self.analyzer.polarity_scores(text)
        compound_score = scores['compound']
        
        # Determine label
        if compound_score >= 0.05:
            polarity = "Positive"
        elif compound_score <= -0.05:
            polarity = "Negative"
        else:
            polarity = "Neutral"
            
        return {
            "polarity": polarity,
            "score": compound_score,
            "details": scores
        }
