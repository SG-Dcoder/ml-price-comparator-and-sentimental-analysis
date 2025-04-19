from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import json
import random
from datetime import datetime
import traceback
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)



# Import scrapers
from scrapers.improved_scrapers import ImprovedAmazonScraper
from scrapers.flipkart_improved_scraper import ImprovedFlipkartScraper

# Import models
from models.price_forecasting import PriceForecaster
from models.sentiment_analysis import SentimentAnalyzer
from models.svm_model import AdvancedSVM

app = Flask(__name__)
app.secret_key = 'price_comparison_secret_key'  # For flash messages

# Initialize scrapers
amazon_scraper = ImprovedAmazonScraper()
flipkart_scraper = ImprovedFlipkartScraper()

# Initialize models
forecaster = PriceForecaster()
sentiment_analyzer = SentimentAnalyzer()
svm_model = AdvancedSVM()

def get_dummy_products(query, platform):
    """Generate dummy products if scraping fails"""
    logger.info(f"Using dummy data for {platform}")
    
    base_price = random.randint(30000, 80000)
    
    products = [
        {
            'name': f'{platform.title()} {query} Pro Max',
            'price': str(base_price),
            'url': f'https://www.{platform}.com/product/dummy1',
            'rating': '4.3'
        },
        {
            'name': f'{platform.title()} {query} Standard Edition',
            'price': str(int(base_price * 0.8)),
            'url': f'https://www.{platform}.com/product/dummy2',
            'rating': '4.1'
        },
        {
            'name': f'{platform.title()} {query} Lite',
            'price': str(int(base_price * 0.6)),
            'url': f'https://www.{platform}.com/product/dummy3',
            'rating': '4.0'
        },
        {
            'name': f'{platform.title()} {query} Ultra Premium',
            'price': str(int(base_price * 1.2)),
            'url': f'https://www.{platform}.com/product/dummy4',
            'rating': '4.7'
        },
        {
            'name': f'{platform.title()} {query} Mini',
            'price': str(int(base_price * 0.4)),
            'url': f'https://www.{platform}.com/product/dummy5',
            'rating': '3.9'
        }
    ]
    return products

def get_dummy_reviews():
    """Generate dummy review data"""
    return {
        'positive': random.randint(30, 80),
        'neutral': random.randint(10, 30),
        'negative': random.randint(5, 20),
        'total_reviews': random.randint(50, 120),
        'reliability_score': random.randint(70, 95)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return redirect(url_for('index'))
        
    query = request.form.get('query')
    if not query:
        flash('Please enter a search query', 'error')
        return redirect(url_for('index'))
    
    logger.info(f"Searching for: {query}")
    
    # First get Amazon products
    try:
        amazon_products = amazon_scraper.search_product(query)
        logger.info(f"Found {len(amazon_products)} products on Amazon")
        if not amazon_products:
            amazon_products = get_dummy_products(query, 'amazon')
    except Exception as e:
        logger.error(f"Error scraping Amazon: {str(e)}")
        traceback.print_exc()
        amazon_products = get_dummy_products(query, 'amazon')
    
    # Then get Flipkart products, passing Amazon products for fallback
    try:
        flipkart_products = flipkart_scraper.search_product(query, amazon_products)
        logger.info(f"Found {len(flipkart_products)} products on Flipkart")
        if not flipkart_products:
            flipkart_products = flipkart_scraper.create_realistic_dummy_products(query, amazon_products)
    except Exception as e:
        logger.error(f"Error scraping Flipkart: {str(e)}")
        traceback.print_exc()
        flipkart_products = flipkart_scraper.create_realistic_dummy_products(query, amazon_products)
    
    all_products = {
        'amazon': amazon_products,
        'flipkart': flipkart_products
    }
    
    # Find the lowest price across platforms
    lowest_price = float('inf')
    best_platform = None
    best_product = None
    
    for platform, products in all_products.items():
        for product in products:
            try:
                price = float(product.get('price', float('inf')))
                if price < lowest_price:
                    lowest_price = price
                    best_platform = platform
                    best_product = product
            except (ValueError, TypeError):
                continue
    
    # Save price data for forecasting
    try:
        if best_product and best_platform:
            if best_platform == 'amazon':
                amazon_scraper.save_price_history(
                    best_product['name'], 
                    lowest_price,
                    'data/price_history/amazon.json'
                )
            elif best_platform == 'flipkart':
                flipkart_scraper.save_price_history(
                    best_product['name'], 
                    lowest_price,
                    'data/price_history/flipkart.json'
                )
            logger.info(f"Saved price history for {best_product['name']} from {best_platform}")
    except Exception as e:
        logger.error(f"Error saving price history: {str(e)}")
    
    # Get reviews for sentiment analysis
    platform_reviews = {}
    for platform, products in all_products.items():
        try:
            if products and 'url' in products[0]:
                if platform == 'amazon':
                    reviews = amazon_scraper.get_product_reviews(products[0]['url'])
                elif platform == 'flipkart':
                    reviews = flipkart_scraper.get_product_reviews(products[0]['url'])
                platform_reviews[platform] = reviews
            else:
                platform_reviews[platform] = get_dummy_reviews()
        except Exception as e:
            logger.error(f"Error getting reviews for {platform}: {str(e)}")
            platform_reviews[platform] = get_dummy_reviews()
    
    # Analyze platform reliability
    try:
        reliability_results = sentiment_analyzer.compare_platforms(platform_reviews)
        logger.info(f"Platform reliability analysis completed")
    except Exception as e:
        logger.error(f"Error analyzing platform reliability: {str(e)}")
        reliability_results = {
            'most_reliable_platform': 'amazon' if random.random() > 0.5 else 'flipkart',
            'reliability_score': random.randint(70, 95),
            'platform_scores': {
                'amazon': get_dummy_reviews(),
                'flipkart': get_dummy_reviews()
            }
        }
    
    # Calculate progress bar widths for platform reliability
    if 'platform_scores' in reliability_results:
        for platform, scores in reliability_results['platform_scores'].items():
            total = scores['total_reviews'] if scores['total_reviews'] > 0 else 1
            scores['positive_width'] = round((scores['positive'] / total) * 100, 1)
            scores['neutral_width'] = round((scores['neutral'] / total) * 100, 1)
            scores['negative_width'] = round((scores['negative'] / total) * 100, 1)
    
    # Prepare response
    response = {
        'query': query,
        'products': all_products,
        'best_deal': {
            'platform': best_platform,
            'product': best_product,
            'price': lowest_price if lowest_price != float('inf') else 'N/A'
        },
        'platform_reliability': reliability_results,
        'search_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # If we have historical data, add price forecast
    try:
        # Combine price history from all platforms for this product
        combined_history = []
        
        for platform in ['amazon', 'flipkart']:
            price_history_file = f'data/price_history/{platform}.json'
            if os.path.exists(price_history_file):
                with open(price_history_file, 'r') as f:
                    try:
                        price_history = json.load(f)
                        # Filter history for this product (fuzzy match)
                        product_history = [
                            item for item in price_history 
                            if query.lower() in item['product'].lower()
                        ]
                        combined_history.extend(product_history)
                    except json.JSONDecodeError:
                        logger.error(f"Error parsing price history JSON for {platform}")
        
        if combined_history:
            logger.info(f"Found {len(combined_history)} historical price points")
            df = forecaster.prepare_data(combined_history)
            if not df.empty:
                forecaster.train_simple_model(df)
                forecast = forecaster.forecast_prices(days=30)
                
                best_time = forecaster.get_best_time_to_buy(forecast)
                forecast_plot = forecaster.get_forecast_plot(df, forecast)
                
                response['price_forecast'] = {
                    'best_time': best_time,
                    'forecast_plot': forecast_plot
                }
                logger.info(f"Price forecast generated successfully")
    except Exception as e:
        logger.error(f"Error generating forecast: {str(e)}")
        traceback.print_exc()
    
    return render_template('results.html', data=response)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('data/price_history', exist_ok=True)
    os.makedirs('data/reviews', exist_ok=True)
    
    logger.info("Starting Flask application on http://127.0.0.1:5000")
    app.run(debug=True)