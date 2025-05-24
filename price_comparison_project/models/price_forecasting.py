import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

class PriceForecaster:
    def __init__(self):
        self.model = None
        self.poly = None
        self.scaler = None
    
    def prepare_data(self, price_history):
        """Convert price history to forecasting-compatible format"""
        df = pd.DataFrame(price_history)
        
        # Handle different date column names
        if 'timestamp' in df.columns:
            df['ds'] = pd.to_datetime(df['timestamp'])
        elif 'date' in df.columns:
            df['ds'] = pd.to_datetime(df['date'])
        else:
            # If no date column, create one
            df['ds'] = pd.to_datetime('today') - pd.to_timedelta(np.arange(len(df)), 'D')
        
        # Handle different price column names
        if 'price' in df.columns:
            df['y'] = pd.to_numeric(df['price'])
        else:
            raise ValueError("No price column found in data")
            
        return df[['ds', 'y']]
    
    def train_simple_model(self, data):
        """
        Train a polynomial regression model for forecasting
        """
        # Convert dates to numeric (days since first date)
        first_date = data['ds'].min()
        data['days'] = (data['ds'] - first_date).dt.days
        
        if len(data) <= 1:
            # Not enough data for regression, return flat forecast
            self.model = {
                'type': 'flat',
                'value': data['y'].mean() if len(data) > 0 else 0,
                'first_date': first_date
            }
        else:
            # Use polynomial regression for better curve fitting
            X = data['days'].values.reshape(-1, 1)
            y = data['y'].values
            
            # Determine degree of polynomial based on data size
            degree = min(3, max(1, len(data) // 3))
            
            self.poly = PolynomialFeatures(degree=degree)
            X_poly = self.poly.fit_transform(X)
            
            # Fit linear regression on polynomial features
            self.model = LinearRegression()
            self.model.fit(X_poly, y)
            
            # Store metadata
            self.metadata = {
                'type': 'polynomial',
                'degree': degree,
                'first_date': first_date
            }
        
        return self.model
    
    def forecast_prices(self, days=30):
        """Forecast prices for the next specified days"""
        if not hasattr(self, 'model') or self.model is None:
            raise Exception("Model not trained yet")
        
        # Generate future dates
        last_date = datetime.now()
        future_dates = [last_date + timedelta(days=i) for i in range(days)]
        
        # Calculate forecasted prices
        if isinstance(self.model, dict) and self.model['type'] == 'flat':
            # Flat forecast (not enough data)
            forecasted_prices = [self.model['value']] * days
            lower_bound = [self.model['value'] * 0.9] * days
            upper_bound = [self.model['value'] * 1.1] * days
        else:
            # Polynomial forecast
            first_date = self.metadata['first_date']
            future_days = np.array([(date - first_date).days for date in future_dates]).reshape(-1, 1)
            
            # Transform to polynomial features
            future_days_poly = self.poly.transform(future_days)
            
            # Predict
            forecasted_prices = self.model.predict(future_days_poly)
            
            # Add confidence intervals (simple approach)
            std_dev = np.std(forecasted_prices) if len(forecasted_prices) > 1 else forecasted_prices[0] * 0.1
            lower_bound = forecasted_prices - 1.96 * std_dev
            upper_bound = forecasted_prices + 1.96 * std_dev
        
        # Create forecast dataframe
        forecast = pd.DataFrame({
            'ds': future_dates,
            'yhat': forecasted_prices,
            'yhat_lower': lower_bound,
            'yhat_upper': upper_bound
        })
        
        return forecast
    
    def get_forecast_plot(self, data, forecast):
        """Generate forecast plot as base64 image"""
        plt.figure(figsize=(10, 6))
        
        # Plot historical data
        if not data.empty:
            plt.scatter(data['ds'], data['y'], color='blue', label='Historical Prices')
        
        # Plot forecast
        plt.plot(forecast['ds'], forecast['yhat'], color='red', label='Forecast')
        plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], 
                         color='red', alpha=0.2, label='Confidence Interval')
        
        plt.title('Price Forecast')
        plt.xlabel('Date')
        plt.ylabel('Price (₹)')
        plt.legend()
        plt.grid(True)
        
        # Format x-axis dates
        plt.gcf().autofmt_xdate()
        
        # Convert plot to base64 string
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return img_str
    
    def get_best_time_to_buy(self, forecast, days=30):
        """Determine the best time to buy based on forecasted prices"""
        min_price_idx = forecast['yhat'].idxmin()
        best_date = forecast.loc[min_price_idx, 'ds']
        predicted_price = forecast.loc[min_price_idx, 'yhat']
        
        # Calculate price drop percentage from current price
        current_price = forecast.loc[0, 'yhat']
        price_drop_pct = ((current_price - predicted_price) / current_price) * 100 if current_price > 0 else 0
        
        return {
            'best_date': best_date.strftime('%Y-%m-%d'),
            'predicted_price': round(predicted_price, 2),
            'price_drop_pct': round(price_drop_pct, 2)
        }