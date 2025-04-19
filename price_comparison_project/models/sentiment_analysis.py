from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

class SentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
    
    def analyze_review_vader(self, review):
        """Analyze sentiment of a single review using VADER"""
        sentiment = self.vader.polarity_scores(review)
        return sentiment
    
    def analyze_review_textblob(self, review):
        """Analyze sentiment of a single review using TextBlob"""
        analysis = TextBlob(review)
        return {
            'polarity': analysis.sentiment.polarity,
            'subjectivity': analysis.sentiment.subjectivity
        }
    
    def analyze_platform_reviews(self, reviews, method='vader'):
        """Analyze all reviews for a platform"""
        if not reviews:
            return {
                'positive': 0,
                'neutral': 0,
                'negative': 0,
                'average_score': 0,
                'reliability_score': 0
            }
        
        positive = 0
        neutral = 0
        negative = 0
        total_compound = 0
        
        for review in reviews:
            if method == 'vader':
                sentiment = self.analyze_review_vader(review)
                score = sentiment['compound']
                
                if score >= 0.05:
                    positive += 1
                elif score <= -0.05:
                    negative += 1
                else:
                    neutral += 1
                
                total_compound += score
            
            elif method == 'textblob':
                sentiment = self.analyze_review_textblob(review)
                score = sentiment['polarity']
                
                if score > 0.1:
                    positive += 1
                elif score < -0.1:
                    negative += 1
                else:
                    neutral += 1
                
                total_compound += score
        
        total_reviews = len(reviews)
        average_score = total_compound / total_reviews if total_reviews > 0 else 0
        
        # Calculate reliability score (0-100)
        # Weighted formula: positive reviews have more impact, negative reviews reduce score
        if total_reviews > 0:
            reliability_score = (positive * 1.5 + neutral * 0.5 - negative * 1.0) / total_reviews * 100
            reliability_score = max(0, min(100, reliability_score))  # Clamp between 0-100
        else:
            reliability_score = 0
        
        return {
            'positive': positive,
            'neutral': neutral,
            'negative': negative,
            'total_reviews': total_reviews,
            'average_score': round(average_score, 2),
            'reliability_score': round(reliability_score, 1)
        }
    
    def compare_platforms(self, platform_reviews):
        """Compare reliability of different platforms"""
        results = {}
        for platform, reviews in platform_reviews.items():
            results[platform] = self.analyze_platform_reviews(reviews)
        
        # Find most reliable platform
        if results:
            most_reliable = max(results.items(), key=lambda x: x[1]['reliability_score'])
            
            return {
                'platform_scores': results,
                'most_reliable_platform': most_reliable[0],
                'reliability_score': most_reliable[1]['reliability_score']
            }
        else:
            return {
                'platform_scores': {},
                'most_reliable_platform': 'N/A',
                'reliability_score': 0
            }