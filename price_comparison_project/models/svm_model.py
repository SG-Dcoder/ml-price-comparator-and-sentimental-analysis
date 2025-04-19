import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler

class AdvancedSVM:
    def __init__(self, kernel='rbf', C=1.0):
        self.kernel = kernel
        self.C = C
        self.model = None
        self.scaler = StandardScaler()
    
    def prepare_features(self, data):
        """
        Extract features from price and review data
        Features: price, price_volatility, avg_rating, review_sentiment, etc.
        """
        features = []
        for item in data:
            feature_vector = [
                float(item.get('price', 0)),
                float(item.get('price_volatility', 0)),
                float(item.get('avg_rating', 0)),
                float(item.get('sentiment_score', 0)),
                float(item.get('reliability_score', 0))
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def train(self, X, y):
        """Train the SVM model with given features and labels"""
        X_scaled = self.scaler.fit_transform(X)
        
        # Initialize SVM model with specified parameters
        self.model = SVC(
            C=self.C,
            kernel=self.kernel,
            probability=True,
            gamma='scale'
        )
        
        # Train the model
        self.model.fit(X_scaled, y)
        
        return self.model
    
    def predict(self, X):
        """Predict using the trained model"""
        if self.model is None:
            raise Exception("Model not trained yet")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """Get probability estimates"""
        if self.model is None:
            raise Exception("Model not trained yet")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)