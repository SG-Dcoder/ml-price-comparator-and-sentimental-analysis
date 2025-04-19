import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta

class PriceForecaster:
    def __init__(self):
        self.model = None
    
    def prepare_data(self, price_history):
        """Convert price history to forecasting-compatible format"""
        df = pd.DataFrame(price_history)
        df['ds'] = pd.to_datetime(df['timestamp'])
        df['y'] = pd.to_numeric(df['price'])
        return df[['ds', 'y']]
    
    def train_simple_model(self, data):
        """
        Train a simple linear regression model for forecasting
        This is a fallback when we don't have enough data for Prophet
        """
        # Convert dates to numeric (days since first date)
        first_date = data['ds'].min()
        data['days'] = (data['ds'] - first_date).dt.days
        
        # Simple linear regression
        if len(data) <= 1:
            # Not enough data for regression, return flat forecast
            slope = 0
            intercept = data['y'].mean() if len(data) > 0 else 0
        else:
            # Calculate slope and intercept
            x = data['days'].values
            y = data['y'].values
            n = len(x)
            slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
            intercept = (np.sum(y) - slope * np.sum(x)) / n
        
        self.model = {'slope': slope, 'intercept': intercept, 'first_date': first_date}
        return self.model
    
    def forecast_prices(self, days=30):
        """Forecast prices for the next specified days using simple model"""
        if not self.model:
            raise Exception("Model not trained yet")
        
        # Generate future dates
        last_date = datetime.now()
        future_dates = [last_date + timedelta(days=i) for i in range(days)]
        
        # Calculate days since first date
        first_date = self.model['first_date']
        future_days = [(date - first_date).days for date in future_dates]
        
        # Calculate forecasted prices
        forecasted_prices = [self.model['intercept'] + self.model['slope'] * day for day in future_days]
        
        # Create forecast dataframe
        forecast = pd.DataFrame({
            'ds': future_dates,
            'yhat': forecasted_prices,
            'yhat_lower': [price * 0.9 for price in forecasted_prices],  # Simple lower bound
            'yhat_upper': [price * 1.1 for price in forecasted_prices]   # Simple upper bound
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
                         color='red', alpha=0.2, label='Uncertainty')
        
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
        
        return {
            'best_date': best_date.strftime('%Y-%m-%d'),
            'predicted_price': round(predicted_price, 2)
        }