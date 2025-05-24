from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import numpy as np
import re

class SentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
    
    def clean_text(self, text):
        """Clean and preprocess text for analysis"""
        if not isinstance(text, str):
            return ""
            
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        # Convert to lowercase
        text = text.lower()
        return text
    
    def analyze_review_vader(self, review):
        """Analyze sentiment of a single review using VADER"""
        cleaned_review = self.clean_text(review)
        if not cleaned_review:
            return {'compound': 0, 'pos': 0, 'neu': 0, 'neg': 0}
            
        sentiment = self.vader.polarity_scores(cleaned_review)
        return sentiment
    
    def analyze_review_textblob(self, review):
        """Analyze sentiment of a single review using TextBlob"""
        cleaned_review = self.clean_text(review)
        if not cleaned_review:
            return {'polarity': 0, 'subjectivity': 0}
            
        analysis = TextBlob(cleaned_review)
        return {
            'polarity': analysis.sentiment.polarity,
            'subjectivity': analysis.sentiment.subjectivity
        }
    
    def analyze_platform_reviews(self, reviews, method='combined'):
        """Analyze all reviews for a platform"""
        # Handle case where reviews is already processed data
        if isinstance(reviews, dict) and 'positive' in reviews:
            return reviews
            
        if not reviews or not isinstance(reviews, list):
            return {
                'positive': 0,
                'neutral': 0,
                'negative': 0,
                'total_reviews': 0,
                'average_score': 0,
                'reliability_score': 0
            }
        
        positive = 0
        neutral = 0
        negative = 0
        total_compound = 0
        
        for review in reviews:
            if method == 'vader' or method == 'combined':
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
            # Calculate weighted score based on positive/negative ratio and review volume
            positive_ratio = positive / total_reviews
            negative_ratio = negative / total_reviews
            
            # Base score from positive/negative ratio
            base_score = (positive_ratio * 100) - (negative_ratio * 50)
            
            # Volume factor - more reviews = more reliable
            volume_factor = min(1.0, total_reviews / 100)  # Caps at 100 reviews
            
            # Final reliability score
            reliability_score = base_score * (0.7 + 0.3 * volume_factor)
            
            # Clamp between 0-100
            reliability_score = max(0, min(100, reliability_score))
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
            
            # Add detailed comparison metrics
            comparison = {
                'platform_scores': results,
                'most_reliable_platform': most_reliable[0],
                'reliability_score': most_reliable[1]['reliability_score'],
                'comparison_metrics': {}
            }
            
            # Add comparison metrics between platforms
            platforms = list(results.keys())
            if len(platforms) >= 2:
                p1, p2 = platforms[0], platforms[1]
                r1, r2 = results[p1], results[p2]
                
                comparison['comparison_metrics'] = {
                    'reliability_difference': abs(r1['reliability_score'] - r2['reliability_score']),
                    'positive_ratio_difference': abs((r1['positive']/max(1, r1['total_reviews'])) - 
                                                   (r2['positive']/max(1, r2['total_reviews']))),
                    'review_volume_ratio': max(r1['total_reviews'], r2['total_reviews']) / 
                                          max(1, min(r1['total_reviews'], r2['total_reviews']))
                }
            
            return comparison
        else:
            return {
                'platform_scores': {},
                'most_reliable_platform': 'N/A',
                'reliability_score': 0,
                'comparison_metrics': {}
            }