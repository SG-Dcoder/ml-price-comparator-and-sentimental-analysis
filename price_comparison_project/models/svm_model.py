import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

class AdvancedSVM:
    def __init__(self, kernel='rbf', C=1.0):
        self.kernel = kernel
        self.C = C
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'price', 'price_volatility', 'avg_rating', 
            'sentiment_score', 'reliability_score'
        ]
    
    def prepare_features(self, products_data):
        """
        Extract features from price and review data
        """
        features = []
        for item in products_data:
            try:
                # Extract price
                price = float(item.get('price', 0))
                
                # Calculate price volatility (if history available)
                price_history = item.get('price_history', [])
                if price_history and len(price_history) > 1:
                    prices = [float(p.get('price', 0)) for p in price_history]
                    price_volatility = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0
                else:
                    price_volatility = 0.0
                
                # Extract rating
                rating_str = item.get('rating', '0')
                # Handle ratings like "4.5 out of 5 stars"
                if isinstance(rating_str, str) and 'out of' in rating_str:
                    rating = float(rating_str.split()[0])
                else:
                    rating = float(rating_str) if rating_str else 0
                
                # Extract sentiment and reliability scores
                reviews = item.get('reviews', {})
                sentiment_score = reviews.get('average_score', 0)
                reliability_score = reviews.get('reliability_score', 0) / 100.0  # Normalize to 0-1
                
                feature_vector = [
                    price,
                    price_volatility,
                    rating,
                    sentiment_score,
                    reliability_score
                ]
                features.append(feature_vector)
            except Exception as e:
                print(f"Error preparing features: {str(e)}")
                # Use default values if extraction fails
                features.append([0, 0, 0, 0, 0])
        
        return np.array(features)
    
    def train(self, X, y):
        """Train the SVM model with given features and labels"""
        if len(X) < 2 or len(np.unique(y)) < 2:
            print("Not enough data or classes for SVM training")
            self.model = None
            return None
            
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data for training and validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Initialize SVM model with specified parameters
        self.model = SVC(
            C=self.C,
            kernel=self.kernel,
            probability=True,
            gamma='scale'
        )
        
        # Train the model
        self.model.fit(X_train, y_train)
        
        # Evaluate on validation set
        val_predictions = self.model.predict(X_val)
        accuracy = accuracy_score(y_val, val_predictions)
        print(f"SVM Model Validation Accuracy: {accuracy:.2f}")
        print(classification_report(y_val, val_predictions))
        
        return self.model
    
    def predict(self, X):
        """Predict using the trained model"""
        if self.model is None:
            print("Model not trained yet, returning default predictions")
            return np.zeros(len(X))
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """Get probability estimates"""
        if self.model is None:
            print("Model not trained yet, returning default probabilities")
            return np.zeros((len(X), 2))
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def get_feature_importance(self):
        """Get approximate feature importance for SVM"""
        if self.model is None or self.kernel != 'linear':
            return {name: 0 for name in self.feature_names}
        
        # For linear kernel, coefficients can be interpreted as feature importance
        importance = {}
        for i, name in enumerate(self.feature_names):
            importance[name] = abs(self.model.coef_[0][i])
        
        return importance