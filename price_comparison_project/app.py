from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
import pymysql
import os
import json
import random
import re
from datetime import datetime, timedelta
import traceback
import logging
import pandas as pd
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash
import concurrent.futures
import time
from functools import lru_cache
from cache import cached
from sqlalchemy import func, select, distinct, text

# Use pymysql as MySQL driver
pymysql.install_as_MySQLdb()

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
from scrapers.amazon_scraper import ImprovedAmazonScraper
from scrapers.flipkart_scraper import ImprovedFlipkartScraper
from scrapers.alibaba_scraper import AlibabaProductScraper
from scrapers.chroma_scraper import ChromaProductScraper
# from scrapers.myntra_scraper import MyntraProductScraper
# from scrapers.ajio_scraper import AjioProductScraper

# Import models
from models.price_forecasting import PriceForecaster
from models.sentiment_analysis import SentimentAnalyzer
from models.svm_model import AdvancedSVM

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pricewizard_secret_key')

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://wizard_user:wizard123@localhost/pricewizard'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 280
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 20

# Import extensions
from extensions import db, migrate, login_manager

# Initialize extensions with app
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)

# Import database models after initializing db
from models.pricewizard_models import User, SearchHistory, PriceHistory, PriceAlert, Product, ProductReview

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.query(User).get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user: {str(e)}")
        return None

# Initialize scrapers with retry mechanisms
amazon_scraper = ImprovedAmazonScraper()
flipkart_scraper = ImprovedFlipkartScraper()
alibaba_scraper = AlibabaProductScraper()
chroma_scraper = ChromaProductScraper()

# Initialize models
forecaster = PriceForecaster()
sentiment_analyzer = SentimentAnalyzer()
svm_model = AdvancedSVM()

def process_search_query(query):
    """Extract product type and key attributes from search query with improved accuracy"""
    # Convert to lowercase for easier matching
    query_lower = query.lower()
    
    # Define product categories and their keywords with more comprehensive coverage
    product_types = {
        "phone": ["iphone", "samsung", "galaxy", "pixel", "xiaomi", "redmi", "oneplus", "smartphone", "mobile", 
                 "poco", "vivo", "oppo", "realme", "mi", "nokia", "motorola", "honor", "phone"],
        "laptop": ["macbook", "laptop", "notebook", "thinkpad", "zenbook", "xps", "vivobook", "ideapad", 
                  "chromebook", "gaming laptop", "ultrabook", "netbook", "pavilion", "envy", "spectre", "inspiron"],
        "tablet": ["ipad", "tab", "tablet", "galaxy tab", "surface", "kindle", "fire hd", "mediapad", "mi pad"],
        "watch": ["watch", "smartwatch", "apple watch", "galaxy watch", "fitbit", "amazfit", "mi band", 
                 "garmin", "fossil", "wear os", "wearable"],
        "headphone": ["airpods", "headphone", "earphone", "earbuds", "headset", "earpods", "neckband", 
                     "wireless earphones", "tws", "noise cancelling", "bluetooth headset"],
        "tv": ["tv", "television", "smart tv", "led tv", "oled", "qled", "android tv", "mi tv", "webos", "tizen"]
    }
    
    # Find the product type with the most keyword matches
    identified_type = None
    max_matches = 0
    
    for product_type, keywords in product_types.items():
        matches = sum(1 for keyword in keywords if keyword in query_lower)
        if matches > max_matches:
            max_matches = matches
            identified_type = product_type
    
    # Extract brand with improved brand list
    brands = ["apple", "samsung", "google", "xiaomi", "oneplus", "sony", "lg", "hp", "dell", "lenovo",
              "asus", "acer", "msi", "huawei", "oppo", "vivo", "realme", "poco", "motorola", "nokia",
              "microsoft", "amazon", "bosch", "philips", "panasonic", "toshiba", "jbl", "bose", "boat"]
    
    identified_brand = None
    for brand in brands:
        # Use word boundary to avoid partial matches
        pattern = r'\b' + re.escape(brand) + r'\b'
        if re.search(pattern, query_lower):
            identified_brand = brand
            break
    
    # Extract model and specifications with improved pattern matching
    model_specs = []
    
    # Look for model numbers/names with more comprehensive patterns
    model_patterns = [
        r'(\d+)\s*(pro|air|max|ultra|plus|\+|mini|lite)',  # 15 Pro, 13 Air, etc.
        r'(s|note|tab|galaxy|pixel)\s*(\d+)',  # S21, Note 20, etc.
        r'(m\d+|a\d+|g\d+)',  # M1, M2, A15 chip
        r'(gen\s*\d+|generation\s*\d+)',  # Gen 5, 10th generation
        r'(\d+th\s*gen)',  # 11th gen
        r'(i\d+)[\-\s](\d+th|\d+)',  # i5-10th, i7-11
        r'(ryzen\s*\d+)',  # Ryzen 7
        r'(gtx|rtx)\s*\d+',  # GTX 1650, RTX 3060
    ]
    
    for pattern in model_patterns:
        matches = re.findall(pattern, query_lower)
        if matches:
            for match in matches:
                if isinstance(match, tuple):
                    model_specs.append(''.join(match).strip())
                else:
                    model_specs.append(match.strip())
    
    # Look for storage capacity
    storage_pattern = r'(\d+)\s*(gb|tb)'
    storage_matches = re.findall(storage_pattern, query_lower)
    if storage_matches:
        for match in storage_matches:
            model_specs.append(''.join(match).strip())
    
    # Look for RAM
    ram_pattern = r'(\d+)\s*(gb|gig)\s*(ram)'
    ram_matches = re.findall(ram_pattern, query_lower)
    if ram_matches:
        for match in ram_matches:
            model_specs.append(''.join(match[:2]).strip() + " RAM")
    
    # Look for screen size
    screen_pattern = r'(\d+[\.\d]*)\s*(inch|\")'
    screen_matches = re.findall(screen_pattern, query_lower)
    if screen_matches:
        for match in screen_matches:
            model_specs.append(''.join(match).strip())
    
    # Extract color if present
    colors = ["black", "white", "blue", "red", "green", "yellow", "purple", "pink", "gold", "silver", "gray", "grey"]
    for color in colors:
        if color in query_lower:
            model_specs.append(color)
            break
    
    return {
        "product_type": identified_type,
        "brand": identified_brand,
        "model_specs": model_specs,
        "original_query": query
    }

def filter_results(products, query_info):
    """Filter search results to exclude accessories and focus on main product with improved accuracy"""
    filtered_products = []
    
    # Keywords that suggest accessories - expanded list
    accessory_keywords = [
        'case', 'cover', 'screen protector', 'screen guard', 'charger', 'cable', 
        'adapter', 'skin', 'stand', 'holder', 'mount', 'dock', 'pouch', 'bag',
        'tempered glass', 'protective', 'shell', 'bumper', 'wallet', 'essentials',
        'sleeve', 'keyboard', 'mouse', 'stylus', 'pen', 'remote', 'controller',
        'silicone', 'glass', 'shield', 'film', 'sticker', 'skin', 'protector',
        'carrying', 'armband', 'grip', 'accessory', 'kit', 'bundle', 'combo'
    ]
    
    # Keywords that must be in the product name for the main product
    required_keywords = []
    
    if query_info["product_type"] == "phone":
        required_keywords = ["phone", "smartphone", "mobile"]
        if query_info["brand"] == "apple":
            required_keywords.append("iphone")
        elif query_info["brand"] == "samsung":
            required_keywords.extend(["galaxy", "samsung"])
        elif query_info["brand"] == "google":
            required_keywords.append("pixel")
    elif query_info["product_type"] == "laptop":
        required_keywords = ["laptop", "notebook"]
        if query_info["brand"] == "apple":
            required_keywords.append("macbook")
        elif query_info["brand"] == "dell":
            required_keywords.extend(["xps", "inspiron", "alienware", "dell"])
    elif query_info["product_type"] == "tablet":
        required_keywords = ["tablet", "tab"]
        if query_info["brand"] == "apple":
            required_keywords.append("ipad")
    elif query_info["product_type"] == "watch":
        required_keywords = ["watch"]
    elif query_info["product_type"] == "headphone":
        required_keywords = ["headphone", "earphone", "earbuds", "headset", "airpods"]
    elif query_info["product_type"] == "tv":
        required_keywords = ["tv", "television"]
    
    # Add model specs to required keywords if they exist
    if query_info["model_specs"]:
        required_keywords.extend(query_info["model_specs"])
    
    # Filter products with improved logic
    for product in products:
        product_name_lower = product['name'].lower()
        
        # Skip products that match accessory keywords
        if any(keyword in product_name_lower for keyword in accessory_keywords):
            # But include if it's specifically what user is looking for
            if "case" in query_info["original_query"].lower() and "case" in product_name_lower:
                filtered_products.append(product)
            continue
        
        # For main products, ensure at least one required keyword is present
        # If no required keywords or if the original query is in the product name
        if (not required_keywords or 
            any(keyword in product_name_lower for keyword in required_keywords) or
            query_info["original_query"].lower() in product_name_lower):
            filtered_products.append(product)
    
    return filtered_products

def calculate_relevance_score(product, query_info):
    """Calculate a relevance score for a product based on how well it matches the query"""
    product_name_lower = product['name'].lower()
    score = 0
    
    # Brand match - increased weight for exact brand match
    if query_info["brand"] and query_info["brand"] in product_name_lower:
        # Check for exact brand match with word boundaries
        pattern = r'\b' + re.escape(query_info["brand"]) + r'\b'
        if re.search(pattern, product_name_lower):
            score += 35  # Increased from 30
        else:
            score += 25  # Partial match
    
    # Product type match with improved scoring
    if query_info["product_type"]:
        product_type_keywords = {
            "phone": ["phone", "smartphone", "mobile"],
            "laptop": ["laptop", "notebook"],
            "tablet": ["tablet", "ipad", "tab"],
            "watch": ["watch"],
            "headphone": ["headphone", "earphone", "earbud", "airpod"],
            "tv": ["tv", "television"]
        }
        
        keywords = product_type_keywords.get(query_info["product_type"], [])
        if any(keyword in product_name_lower for keyword in keywords):
            score += 30  # Increased from 25
    
    # Model specifications match with improved scoring
    for spec in query_info["model_specs"]:
        spec_lower = spec.lower()
        # Check for exact spec match with word boundaries
        pattern = r'\b' + re.escape(spec_lower) + r'\b'
        if re.search(pattern, product_name_lower):
            score += 20  # Increased from 15 for exact match
        elif spec_lower in product_name_lower:
            score += 15  # Partial match
    
    # Exact phrase match
    if query_info["original_query"].lower() in product_name_lower:
        score += 45  # Increased from 40
    
    # Penalize accessories unless specifically searching for them
    accessory_keywords = [
        'case', 'cover', 'screen protector', 'screen guard', 'charger', 'cable', 
        'adapter', 'skin', 'stand', 'holder'
    ]
    
    if any(keyword in product_name_lower for keyword in accessory_keywords) and not any(keyword in query_info["original_query"].lower() for keyword in accessory_keywords):
        score -= 60  # Increased penalty from 50
    
    # Bonus for price presence - products with actual prices should rank higher
    try:
        if 'price' in product and product['price'] and float(product['price']) > 0:
            score += 10
    except (ValueError, TypeError):
        pass
    
    # Bonus for rating presence
    if 'rating' in product and product['rating']:
        try:
            rating = float(product['rating'])
            if rating > 4.0:
                score += 5
            elif rating > 3.5:
                score += 3
        except (ValueError, TypeError):
            pass
    
    # Bonus for image presence
    if 'image_url' in product and product['image_url'] and not product['image_url'].endswith('placeholder'):
        score += 5
    
    return score

def timeout_scraper(func, args=(), kwargs={}, timeout_duration=10, default=None):
    """Run a function with a timeout"""
    import signal
    
    class TimeoutError(Exception):
        pass
    
    def handler(signum, frame):
        raise TimeoutError()
    
    # Set the timeout handler
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout_duration)
    
    try:
        result = func(*args, **kwargs)
    except TimeoutError:
        result = default
    finally:
        signal.alarm(0)
    
    return result

def get_dummy_products(query, platform):
    """Generate dummy products if scraping fails with improved realism"""
    logger.info(f"Using dummy data for {platform}")
    
    # Make base price more realistic based on product type
    query_info = process_search_query(query)
    
    # Set base price range based on product type
    if query_info["product_type"] == "phone":
        base_price = random.randint(15000, 120000)
    elif query_info["product_type"] == "laptop":
        base_price = random.randint(35000, 150000)
    elif query_info["product_type"] == "tablet":
        base_price = random.randint(15000, 80000)
    elif query_info["product_type"] == "watch":
        base_price = random.randint(2000, 45000)
    elif query_info["product_type"] == "headphone":
        base_price = random.randint(1000, 30000)
    elif query_info["product_type"] == "tv":
        base_price = random.randint(15000, 120000)
    else:
        base_price = random.randint(5000, 50000)
    
    # Generate more realistic product names based on query
    brand = query_info["brand"].title() if query_info["brand"] else platform.title()
    product_type = query_info["product_type"] if query_info["product_type"] else "Product"
    
    # Generate model variants
    variants = ["Pro", "Max", "Ultra", "Standard", "Lite", "Plus", "Premium", "Basic", "Mini"]
    specs = ["128GB", "256GB", "512GB", "1TB", "8GB RAM", "16GB RAM", "32GB RAM"]
    
    products = []
    for i in range(5):
        variant = random.choice(variants)
        spec = random.choice(specs)
        
        # Adjust price based on variant
        price_multiplier = 1.0
        if variant == "Pro" or variant == "Premium":
            price_multiplier = 1.2
        elif variant == "Max" or variant == "Ultra":
            price_multiplier = 1.4
        elif variant == "Lite" or variant == "Basic" or variant == "Mini":
            price_multiplier = 0.8
        
        # Create product name
        if query_info["brand"]:
            product_name = f"{brand} {query} {variant} {spec}"
        else:
            product_name = f"{platform.title()} {query} {variant} {spec}"
        
        # Create product
        products.append({
            'name': product_name,
            'price': str(int(base_price * price_multiplier)),
            'url': f'https://www.{platform}.com/product/dummy{i+1}',
            'rating': str(round(random.uniform(3.5, 4.9), 1)),
            'image_url': f'https://via.placeholder.com/200x200?text={platform}+{query}+{variant}'
        })
    
    return products

def get_dummy_reviews():
    """Generate dummy review data with more realistic distribution"""
    # Generate a more realistic distribution of reviews
    total_reviews = random.randint(50, 500)
    
    # Calculate positive, neutral and negative reviews
    # Most products have more positive than negative reviews
    positive_ratio = random.uniform(0.6, 0.85)  # 60-85% positive
    neutral_ratio = random.uniform(0.1, 0.25)   # 10-25% neutral
    negative_ratio = 1 - positive_ratio - neutral_ratio  # Remaining negative
    
    positive = int(total_reviews * positive_ratio)
    neutral = int(total_reviews * neutral_ratio)
    negative = total_reviews - positive - neutral  # Ensure they add up to total
    
    # Calculate reliability score using the corrected method
    reliability_score = calculate_reliability_score(positive, neutral, negative)
    
    return {
        'positive': positive,
        'neutral': neutral,
        'negative': negative,
        'total_reviews': total_reviews,
        'reliability_score': reliability_score,
        'is_real_data': False
    }

def calculate_reliability_score(positive, neutral, negative):
    """Calculate a reliability score based on sentiment distribution using the correct formula."""
    total = positive + neutral + negative
    if total == 0:
        return 0
    
    # Correct formula: (positive * 100 + neutral * 50) / (total * 100) * 100
    reliability_score = (positive * 100 + neutral * 50) / (total * 100) * 100
    
    # Ensure score is within 0-100 range
    final_score = max(0, min(100, reliability_score))
    return round(final_score)

def save_search_history(query, user_id=None):
    """Save search history to database with improved error handling"""
    try:
        # Check if this exact search already exists for this user in the last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        if user_id:
            existing_search = db.session.query(SearchHistory).filter(
                SearchHistory.query == query,
                SearchHistory.user_id == user_id,
                SearchHistory.timestamp >= one_hour_ago
            ).first()
        else:
            existing_search = db.session.query(SearchHistory).filter(
                SearchHistory.query == query,
                SearchHistory.user_id.is_(None),
                SearchHistory.timestamp >= one_hour_ago
            ).first()
        
        # Only save if not a duplicate recent search
        if not existing_search:
            search = SearchHistory(query=query, user_id=user_id)
            db.session.add(search)
            db.session.commit()
            logger.info(f"Search history saved: {query} for user_id: {user_id}")
        else:
            logger.info(f"Duplicate search not saved: {query} for user_id: {user_id}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving search history: {str(e)}")

@cached(expiry=3600)  # Cache for 1 hour
def get_cached_products(query, platform):
    """Cache product results to avoid repeated scraping for the same query"""
    try:
        if platform == 'amazon':
            return amazon_scraper.search_product(query)
        elif platform == 'flipkart':
            amazon_products = get_cached_products(query, 'amazon')
            return flipkart_scraper.search_product(query, amazon_products)
        elif platform == 'alibaba':
            return alibaba_scraper.search_product(query)
        elif platform == 'croma':
            return chroma_scraper.search_product(query)
        return []
    except Exception as e:
        logger.error(f"Error in get_cached_products for {platform}: {str(e)}")
        return []

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.authenticate(username, password)
        
        if user:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input with improved validation
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('signup.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')
        
        # Validate email format
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            flash('Please enter a valid email address', 'danger')
            return render_template('signup.html')
        
        # Validate password strength
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return render_template('signup.html')
        
        # Create user
        user = User.create_user(username, email, password)
        
        if user:
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists', 'danger')
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    # Get user's saved searches with improved query
    saved_searches = []
    try:
        user_searches = db.session.query(SearchHistory).filter_by(user_id=current_user.id).order_by(SearchHistory.timestamp.desc()).limit(20).all()
        
        for search in user_searches:
            saved_searches.append({
                'query': search.query,
                'date': search.timestamp.strftime('%Y-%m-%d %H:%M')
            })
    except Exception as e:
        logger.error(f"Error fetching user searches: {str(e)}")
        flash('Error loading your search history', 'danger')
    
    # Get user's price alerts with improved query
    price_alerts = []
    try:
        alerts = db.session.query(PriceAlert).filter_by(user_id=current_user.id).all()
        
        for alert in alerts:
            price_alerts.append({
                'id': alert.id,
                'product_name': alert.product_name,
                'target_price': alert.target_price,
                'current_price': alert.current_price,
                'platform': alert.platform,
                'status': alert.status,
                'created_at': alert.created_at.strftime('%Y-%m-%d')
            })
    except Exception as e:
        logger.error(f"Error fetching price alerts: {str(e)}")
        flash('Error loading your price alerts', 'danger')
    
    return render_template('profile.html', 
                          saved_searches=saved_searches, 
                          price_alerts=price_alerts)

@app.route('/')
def index():
    # Redirect to login page if user is not authenticated
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # Get recent searches for the current user
    saved_searches = []
    try:
        user_searches = db.session.query(SearchHistory).filter_by(user_id=current_user.id).order_by(SearchHistory.timestamp.desc()).limit(5).all()    
        for search in user_searches:
            saved_searches.append({
                'query': search.query,
                'date': search.timestamp.strftime('%Y-%m-%d %H:%M')
            })
    except Exception as e:
        logger.error(f"Error fetching recent searches: {str(e)}")
    
    # Get trending searches
    trending_searches = []
    try:
        # Get most popular searches in the last week
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        popular_searches = db.session.query(
            SearchHistory.query, 
            func.count(SearchHistory.id).label('count')
        ).filter(
            SearchHistory.timestamp >= one_week_ago
        ).group_by(
            SearchHistory.query
        ).order_by(
            text('count DESC')
        ).limit(5).all()
        
        trending_searches = [search[0] for search in popular_searches]
    except Exception as e:
        logger.error(f"Error fetching trending searches: {str(e)}")
    
    return render_template('index.html', saved_searches=saved_searches, trending_searches=trending_searches)

@app.route('/guest')
def guest_search():
    # Allow users to search without logging in
    # Get trending searches for guest users too
    trending_searches = []
    try:
        # Get most popular searches in the last week
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        popular_searches = db.session.query(
            SearchHistory.query, 
            func.count(SearchHistory.id).label('count')
        ).filter(
            SearchHistory.timestamp >= one_week_ago
        ).group_by(
            SearchHistory.query
        ).order_by(
            text('count DESC')
        ).limit(5).all()
        
        trending_searches = [search[0] for search in popular_searches]
    except Exception as e:
        logger.error(f"Error fetching trending searches for guest: {str(e)}")
    
    return render_template('index.html', saved_searches=[], trending_searches=trending_searches)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return redirect(url_for('index'))
        
    start_time = time.time()
    query = request.form.get('query')
    if not query:
        flash('Please enter a search query', 'error')
        return redirect(url_for('index'))
    
    logger.info(f"Searching for: {query}")
    
    # Process the search query to extract product type, brand, and specifications
    query_info = process_search_query(query)
    logger.info(f"Processed query info: {query_info}")
    
    # Save search history if user is logged in
    if current_user.is_authenticated:
        save_search_history(query, current_user.id)
    else:
        save_search_history(query)
    
    # Get products from all platforms using parallel processing
    all_products = {}
    platform_reviews = {}
    
    # Define platforms
    platforms = ['amazon', 'flipkart', 'alibaba', 'croma']
    
    # Function to scrape a single platform
    def scrape_platform(platform):
        try:
            # Try to get from cache first
            products = get_cached_products(query, platform)
            if not products or len(products) == 0:
                if platform == 'amazon':
                    products = get_dummy_products(query, 'amazon')
                elif platform == 'flipkart':
                    amazon_products = all_products.get('amazon', [])
                    products = flipkart_scraper.create_realistic_dummy_products(query, amazon_products)
                else:
                    products = get_dummy_products(query, platform)
            
            # Filter products to exclude accessories
            filtered_products = filter_results(products, query_info)
            
            # Calculate relevance score for each product
            for product in filtered_products:
                product['relevance_score'] = calculate_relevance_score(product, query_info)
            
            # Sort by relevance score (highest first)
            filtered_products = sorted(filtered_products, key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            return platform, filtered_products, None
        except Exception as e:
            logger.error(f"Error scraping {platform}: {str(e)}")
            logger.error(traceback.format_exc())
            return platform, get_dummy_products(query, platform), e
    
    # First, get Amazon products (needed for Flipkart)
    try:
        amazon_result = scrape_platform('amazon')
        all_products[amazon_result[0]] = amazon_result[1]
    except Exception as e:
        logger.error(f"Error in Amazon scraping: {str(e)}")
        logger.error(traceback.format_exc())
        all_products['amazon'] = get_dummy_products(query, 'amazon')
    
    # Then get other platforms in parallel with improved error handling
    other_platforms = [p for p in platforms if p != 'amazon']
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_platform = {executor.submit(scrape_platform, platform): platform for platform in other_platforms}
        for future in concurrent.futures.as_completed(future_to_platform):
            platform = future_to_platform[future]
            try:
                platform, products, error = future.result()
                all_products[platform] = products
                if error:
                    logger.warning(f"Used fallback for {platform} due to: {error}")
            except Exception as e:
                logger.error(f"Exception for {platform}: {str(e)}")
                logger.error(traceback.format_exc())
                all_products[platform] = get_dummy_products(query, platform)
    
    # Find the lowest price across all platforms
    lowest_price = float('inf')
    best_platform = None
    best_product = None
    
    for platform, products in all_products.items():
        for product in products:
            try:
                # Skip products without a price
                if 'price' not in product or not product['price']:
                    continue
                    
                # Try to convert price to float
                price_str = product['price']
                # Remove any currency symbols and commas
                price_str = re.sub(r'[^\d.]', '', price_str)
                price = float(price_str)
                
                if price > 0 and price < lowest_price:
                    lowest_price = price
                    best_platform = platform
                    best_product = product
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing price for product: {product.get('name', 'Unknown')}: {str(e)}")
                continue
    
    # Save price data for forecasting (do this asynchronously)
    if best_product and best_platform and lowest_price != float('inf'):
        try:
            # Check if this product already exists in the database
            existing_product = db.session.query(PriceHistory).filter_by(
                product_name=best_product['name'],
                platform=best_platform
            ).order_by(PriceHistory.timestamp.desc()).first()
            
            # Only add if price is different or product doesn't exist
            if not existing_product or abs(existing_product.price - lowest_price) > 1:
                price_history = PriceHistory(
                    product_name=best_product['name'],
                    platform=best_platform,
                    price=float(lowest_price),
                    url=best_product.get('url', '')
                )
                db.session.add(price_history)
                db.session.commit()
                logger.info(f"Saved price history for {best_product['name']}")
            else:
                logger.info(f"Skipped saving duplicate price for {best_product['name']}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving price history: {str(e)}")
    
    # Get reviews in parallel with improved error handling
    def get_platform_reviews(platform):
        try:
            if platform not in all_products or not all_products[platform]:
                return platform, get_dummy_reviews()
            
            products = all_products[platform]
            if not products or len(products) == 0 or 'url' not in products[0]:
                return platform, get_dummy_reviews()
            
            # Set a timeout for review scraping to prevent long delays
            if platform == 'amazon':
                reviews = timeout_scraper(amazon_scraper.get_product_reviews, args=(products[0]['url'],), timeout_duration=8, default=get_dummy_reviews())
            elif platform == 'flipkart':
                reviews = timeout_scraper(flipkart_scraper.get_product_reviews, args=(products[0]['url'],), timeout_duration=8, default=get_dummy_reviews())
            elif platform == 'alibaba':
                reviews = timeout_scraper(alibaba_scraper.get_product_reviews, args=(products[0]['url'],), timeout_duration=8, default=get_dummy_reviews())
            elif platform == 'croma':
                reviews = timeout_scraper(chroma_scraper.get_product_reviews, args=(products[0]['url'],), timeout_duration=8, default=get_dummy_reviews())
            else:
                reviews = get_dummy_reviews()
                
            # If no reviews were found, use dummy data
            if not reviews or 'total_reviews' not in reviews or reviews['total_reviews'] == 0:
                reviews = get_dummy_reviews()
                
            return platform, reviews
        except Exception as e:
            logger.error(f"Error getting reviews for {platform}: {str(e)}")
            return platform, get_dummy_reviews()
    
    # Get reviews in parallel with improved error handling
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_to_platform = {executor.submit(get_platform_reviews, platform): platform for platform in platforms}
        for future in concurrent.futures.as_completed(future_to_platform):
            platform = future_to_platform[future]
            try:
                platform, reviews = future.result()
                platform_reviews[platform] = reviews
            except Exception as e:
                logger.error(f"Exception getting reviews for {platform}: {str(e)}")
                platform_reviews[platform] = get_dummy_reviews()
    
    # Calculate platform reliability scores
    try:
        # Recalculate reliability scores to ensure they're correct
        for platform, reviews in platform_reviews.items():
            reviews['reliability_score'] = calculate_reliability_score(
                reviews['positive'], 
                reviews['neutral'], 
                reviews['negative']
            )
        
        # Find most reliable platform
        most_reliable_platform = max(platform_reviews.items(), key=lambda x: x[1]['reliability_score'])[0]
        reliability_score = platform_reviews[most_reliable_platform]['reliability_score']
        
        reliability_results = {
            'most_reliable_platform': most_reliable_platform,
            'reliability_score': reliability_score,
            'platform_scores': platform_reviews
        }
    except Exception as e:
        logger.error(f"Error analyzing platform reliability: {str(e)}")
        # Generate dummy reliability results
        reliability_results = {
            'most_reliable_platform': 'amazon',
            'reliability_score': 85,
            'platform_scores': platform_reviews
        }
    
    # Calculate progress bar widths for platform reliability
    if 'platform_scores' in reliability_results:
        for platform, scores in reliability_results['platform_scores'].items():
            total = scores['total_reviews'] if scores['total_reviews'] > 0 else 1
            scores['positive_width'] = round((scores['positive'] / total) * 100, 1)
            scores['neutral_width'] = round((scores['neutral'] / total) * 100, 1)
            scores['negative_width'] = round((scores['negative'] / total) * 100, 1)
    
    # Prepare debug information
    debug_info = {
        'platform_calculations': {},
        'execution_time': round(time.time() - start_time, 2),
        'query_info': query_info  # Add query info to debug data
    }
    for platform, reviews in platform_reviews.items():
        debug_info['platform_calculations'][platform] = {
            'positive': reviews['positive'],
            'neutral': reviews['neutral'],
            'negative': reviews['negative'],
            'score': reviews['reliability_score']
        }
    
    # Prepare response
    response = {
        'query': query,
        'query_info': query_info,  # Add query info to response
        'products': all_products,
        'best_deal': {
            'platform': best_platform,
            'product': best_product,
            'price': lowest_price if lowest_price != float('inf') else 'N/A'
        },
        'platform_reliability': reliability_results,
        'search_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'execution_time': debug_info['execution_time'],
        'debug_info': debug_info
    }
    
    # Simplify response for faster rendering
    # Skip historical data and forecasting if response is already taking too long
    if time.time() - start_time > 5:
        logger.warning("Search taking too long, skipping historical data and forecasting")
        return render_template('results.html', data=response)
    
    # Add historical price data and trends for the best product (if time permits)
    try:
        if best_product and best_platform:
            # Get historical price data from database
            product_name = best_product['name']
            
            # Query the database for price history
            price_history_records = db.session.query(PriceHistory).filter_by(
                product_name=product_name,
                platform=best_platform
            ).order_by(PriceHistory.timestamp).all()
            
            combined_history = []
            
            # Convert database records to dictionary format
            for record in price_history_records:
                combined_history.append({
                    'product': record.product_name,
                    'price': str(record.price),
                    'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'platform': best_platform.title(),
                    'url': record.url
                })
            
            # Add to response
            if combined_history:
                # Prepare chart data
                chart_labels = [item.get('timestamp', '').split(' ')[0] for item in combined_history]
                chart_data = {}
                
                # Initialize all platforms with null data
                for platform in platforms:
                    chart_data[platform] = [None] * len(chart_labels)
                
                # Add data for the best platform
                for i, item in enumerate(combined_history):
                    platform = best_platform
                    try:
                        chart_data[platform][i] = float(item['price'])
                    except (ValueError, IndexError):
                        pass
                
                # Add chart data to response
                chart_data['labels'] = chart_labels
                
                # Calculate trends
                trends = {}
                if len(combined_history) >= 2:
                    prices = [float(item['price']) for item in combined_history]
                    first_price = prices[0]
                    last_price = prices[-1]
                    
                    # Overall trend
                    if first_price > 0:
                        overall_change = ((last_price - first_price) / first_price) * 100
                        trends['overall'] = round(overall_change, 1)
                    else:
                        trends['overall'] = None
                    
                    # Last week trend (if we have enough data)
                    if len(prices) >= 7:
                        week_ago_price = prices[-7] if len(prices) >= 7 else prices[0]
                        if week_ago_price > 0:
                            week_change = ((last_price - week_ago_price) / week_ago_price) * 100
                            trends['last_week'] = round(week_change, 1)
                        else:
                            trends['last_week'] = None
                    else:
                        trends['last_week'] = None
                    
                    # Last month trend
                    if len(prices) >= 30:
                        month_ago_price = prices[-30] if len(prices) >= 30 else prices[0]
                        if month_ago_price > 0:
                            month_change = ((last_price - month_ago_price) / month_ago_price) * 100
                            trends['last_month'] = round(month_change, 1)
                        else:
                            trends['last_month'] = None
                    else:
                        trends['last_month'] = None
                    
                    # Lowest and highest ever
                    trends['lowest_ever'] = min(prices)
                    trends['highest_ever'] = max(prices)
                else:
                    trends = {
                        'overall': None,
                        'last_week': None,
                        'last_month': None,
                        'lowest_ever': float(combined_history[0]['price']) if combined_history else None,
                        'highest_ever': float(combined_history[0]['price']) if combined_history else None
                    }
                
                response['price_history'] = {
                    'history': combined_history,
                    'chart_data': chart_data,
                    'trends': trends
                }
    except Exception as e:
        logger.error(f"Error preparing price history: {str(e)}")
        logger.error(traceback.format_exc())
    
    # Skip SVM analysis to save time
    response['svm_analysis'] = {
        'trained': False,
        'message': 'SVM analysis skipped for performance'
    }
    
    logger.info(f"Search completed in {debug_info['execution_time']} seconds")
    return render_template('results.html', data=response)

@app.route('/quick-search', methods=['POST'])
def quick_search():
    query = request.form.get('query')
    if not query:
        return jsonify({'error': 'No query provided'})
    
    # Process the query to extract product type and attributes
    query_info = process_search_query(query)
    
    # Only search Amazon for quick results with improved error handling
    try:
        # Try to get cached results first
        products = get_cached_products(query, 'amazon')
        
        # If no cached results, use dummy data
        if not products or len(products) == 0:
            products = get_dummy_products(query, 'amazon')
        
        # Limit to 10 results for filtering
        products = products[:10]
        
        # Filter products to exclude accessories
        filtered_products = filter_results(products, query_info)
        
        # Calculate relevance score for each product
        for product in filtered_products:
            product['relevance_score'] = calculate_relevance_score(product, query_info)
        
        # Sort by relevance score and limit to 5 results
        filtered_products = sorted(filtered_products, key=lambda x: x.get('relevance_score', 0), reverse=True)[:5]
        
        return jsonify({
            'products': filtered_products,
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error in quick search: {str(e)}")
        logger.error(traceback.format_exc())
        # Return dummy products on error
        dummy_products = get_dummy_products(query, 'amazon')[:5]
        return jsonify({
            'products': dummy_products,
            'status': 'error',
            'error': str(e)
        })

@app.route('/dashboard')
def dashboard():
    try:
        # Get recent search history (limit to 10)
        try:
            recent_searches = SearchHistory.query.order_by(SearchHistory.timestamp.desc()).limit(10).all()
        except Exception as e:
            logger.error(f"Error fetching search history: {str(e)}")
            recent_searches = []
        
        # Get price history data for chart
        try:
            price_history_data = PriceHistory.query.order_by(PriceHistory.timestamp.desc()).limit(100).all()
            chart_data = process_price_history_for_chart(price_history_data)
        except Exception as e:
            logger.error(f"Error processing price history: {str(e)}")
            # Use sample chart data
            chart_data = {
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'datasets': [
                    {
                        'label': 'iPhone 13 (Amazon)',
                        'data': [79999, 78999, 77999, 76999, 75999, 74999],
                        'backgroundColor': 'rgba(255, 153, 0, 0.7)',
                        'borderColor': 'rgba(255, 153, 0, 1)',
                        'fill': False
                    },
                    {
                        'label': 'iPhone 13 (Flipkart)',
                        'data': [80999, 79999, 78999, 77999, 76999, 75999],
                        'backgroundColor': 'rgba(40, 116, 240, 0.7)',
                        'borderColor': 'rgba(40, 116, 240, 1)',
                        'fill': False
                    }
                ]
            }
        
        # Get platform reliability scores
        try:
            platform_reliability = get_platform_reliability_scores()
        except Exception as e:
            logger.error(f"Error getting platform reliability: {str(e)}")
            platform_reliability = {
                'platform_scores': {
                    'amazon': {'positive': 120, 'neutral': 30, 'negative': 10, 'reliability_score': 85},
                    'flipkart': {'positive': 100, 'neutral': 40, 'negative': 15, 'reliability_score': 80},
                    'alibaba': {'positive': 80, 'neutral': 35, 'negative': 20, 'reliability_score': 75},
                    'croma': {'positive': 70, 'neutral': 30, 'negative': 15, 'reliability_score': 78}
                },
                'most_reliable_platform': 'amazon',
                'reliability_score': 85
            }
        
        # Get recent price alerts
        try:
            price_alerts = PriceAlert.query.filter_by(status='Active').order_by(PriceAlert.created_at.desc()).limit(5).all()
        except Exception as e:
            logger.error(f"Error fetching price alerts: {str(e)}")
            price_alerts = []
        
        # Get trending products
        try:
            trending_products = get_trending_products()
        except Exception as e:
            logger.error(f"Error getting trending products: {str(e)}")
            trending_products = [
                {'name': 'iPhone 13', 'platform': 'amazon', 'price': 74999, 'url': '#', 'trend_score': 120},
                {'name': 'Samsung Galaxy S22', 'platform': 'flipkart', 'price': 65999, 'url': '#', 'trend_score': 100},
                {'name': 'MacBook Pro', 'platform': 'amazon', 'price': 129999, 'url': '#', 'trend_score': 95},
                {'name': 'OnePlus 10T', 'platform': 'croma', 'price': 45999, 'url': '#', 'trend_score': 85},
                {'name': 'iPad Air', 'platform': 'amazon', 'price': 54999, 'url': '#', 'trend_score': 80}
            ]
        
        # Get price drop statistics
        try:
            price_drops = get_price_drop_statistics()
        except Exception as e:
            logger.error(f"Error getting price drop statistics: {str(e)}")
            price_drops = {
                'total_drops': 15,
                'average_drop': 8.5,
                'biggest_drop': {
                    'product': 'Samsung Galaxy S22 Ultra',
                    'platform': 'amazon',
                    'drop_percentage': 15.3,
                    'old_price': 109999,
                    'new_price': 93199
                }
            }
        
        return render_template('dashboard.html', 
                              recent_searches=recent_searches,
                              chart_data=chart_data,
                              platform_reliability=platform_reliability,
                              price_alerts=price_alerts,
                              trending_products=trending_products,
                              price_drops=price_drops)
    
    except Exception as e:
        # Log the error
        logger.error(f"Dashboard error: {str(e)}")
        logger.error(traceback.format_exc())
        # Return a simple error message
        return f"""
        <h1>Dashboard Error</h1>
        <p>An error occurred while loading the dashboard: {str(e)}</p>
        <p><a href="/">Return to Home</a></p>
        """, 500

# New function to get price drop statistics
def get_price_drop_statistics():
    """Get statistics about recent price drops"""
    price_drops = {
        'total_drops': 0,
        'average_drop': 0,
        'biggest_drop': None
    }
    
    try:
        # Get data from the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Get all products with price history
        products = db.session.query(distinct(PriceHistory.product_name)).all()
        products = [p[0] for p in products]
        
        drops = []
        biggest_drop = None
        biggest_drop_percentage = 0
        
        for product in products:
            # Get price history for this product
            history = db.session.query(PriceHistory).filter(
                PriceHistory.product_name == product,
                PriceHistory.timestamp >= thirty_days_ago
            ).order_by(PriceHistory.timestamp).all()
            
            if len(history) >= 2:
                # Group by platform
                by_platform = {}
                for item in history:
                    if item.platform not in by_platform:
                        by_platform[item.platform] = []
                    by_platform[item.platform].append(item)
                
                # Check each platform for price drops
                for platform, items in by_platform.items():
                    if len(items) >= 2:
                        first_price = items[0].price
                        last_price = items[-1].price
                        
                        if last_price < first_price:
                            drop_percentage = ((first_price - last_price) / first_price) * 100
                            drops.append(drop_percentage)
                            
                            # Check if this is the biggest drop
                            if drop_percentage > biggest_drop_percentage:
                                biggest_drop_percentage = drop_percentage
                                biggest_drop = {
                                    'product': product,
                                    'platform': platform,
                                    'drop_percentage': round(drop_percentage, 1),
                                    'old_price': round(first_price, 2),
                                    'new_price': round(last_price, 2)
                                }
        
        # Calculate statistics
        price_drops['total_drops'] = len(drops)
        if drops:
            price_drops['average_drop'] = round(sum(drops) / len(drops), 1)
        price_drops['biggest_drop'] = biggest_drop
    
    except Exception as e:
        logger.error(f"Error in get_price_drop_statistics: {str(e)}")
        logger.error(traceback.format_exc())
        # Return default values
        price_drops = {
            'total_drops': 0,
            'average_drop': 0,
            'biggest_drop': None
        }
    
    return price_drops

def process_price_history_for_chart(price_history_data):
    # Process price history data into a format suitable for Chart.js
    chart_data = {
        'labels': [],
        'datasets': []
    }
    
    try:
        # Group data by platform and product
        grouped_data = {}
        for item in price_history_data:
            key = f"{item.platform}_{item.product_name}"
            if key not in grouped_data:
                grouped_data[key] = {
                    'platform': item.platform,
                    'product_name': item.product_name,
                    'prices': [],
                    'timestamps': []
                }
            grouped_data[key]['prices'].append(item.price)
            grouped_data[key]['timestamps'].append(item.timestamp.strftime('%Y-%m-%d'))
        
        # Create datasets for chart
        colors = {
            'amazon': 'rgba(255, 153, 0, 0.7)',
            'flipkart': 'rgba(40, 116, 240, 0.7)',
            'alibaba': 'rgba(255, 106, 0, 0.7)',
            'croma': 'rgba(17, 151, 68, 0.7)'
        }
        
        # Limit to top 5 products to avoid cluttering the chart
        top_products = sorted(grouped_data.items(), key=lambda x: len(x[1]['prices']), reverse=True)[:5]
        
        for key, data in top_products:
            chart_data['datasets'].append({
                'label': f"{data['product_name'][:20]}... ({data['platform']})",
                'data': data['prices'],
                'backgroundColor': colors.get(data['platform'].lower(), 'rgba(128, 128, 128, 0.7)'),
                'borderColor': colors.get(data['platform'].lower(), 'rgba(128, 128, 128, 1)'),
                'fill': False
            })
            
            # Add timestamps to labels if not already there
            for timestamp in data['timestamps']:
                if timestamp not in chart_data['labels']:
                    chart_data['labels'].append(timestamp)
        
        # Sort labels chronologically
        chart_data['labels'] = sorted(chart_data['labels'])
        
        # Limit number of labels to avoid cluttering
        if len(chart_data['labels']) > 10:
            step = len(chart_data['labels']) // 10
            chart_data['labels'] = chart_data['labels'][::step]
    except Exception as e:
        logger.error(f"Error in process_price_history_for_chart: {str(e)}")
        logger.error(traceback.format_exc())
        # Return empty chart data on error
        chart_data = {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'datasets': [{
                'label': 'Sample Data',
                'data': [50000, 49000, 48000, 47000, 46000, 45000],
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'fill': False
            }]
        }
    
    return chart_data

def get_platform_reliability_scores():
    # Get platform reliability scores based on product reviews
    platforms = ['amazon', 'flipkart', 'alibaba', 'croma']
    reliability_data = {}
    
    try:
        for platform in platforms:
            # Count reviews by sentiment
            positive = ProductReview.query.filter_by(platform=platform, sentiment='positive').count()
            neutral = ProductReview.query.filter_by(platform=platform, sentiment='neutral').count()
            negative = ProductReview.query.filter_by(platform=platform, sentiment='negative').count()
            
            total = positive + neutral + negative
            if total > 0:
                reliability_score = int((positive * 100 + neutral * 50) / (total * 100) * 100)
            else:
                reliability_score = 0
            
            reliability_data[platform] = {
                'positive': positive,
                'neutral': neutral,
                'negative': negative,
                'reliability_score': reliability_score
            }
        
        # Find most reliable platform
        if reliability_data:
            most_reliable = max(reliability_data.items(), key=lambda x: x[1]['reliability_score'])
            most_reliable_platform = most_reliable[0]
            reliability_score = most_reliable[1]['reliability_score']
        else:
            most_reliable_platform = 'amazon'
            reliability_score = 0
    except Exception as e:
        logger.error(f"Error in get_platform_reliability_scores: {str(e)}")
        logger.error(traceback.format_exc())
        # Return sample data on error
        return {
            'platform_scores': {
                'amazon': {'positive': 120, 'neutral': 30, 'negative': 10, 'reliability_score': 85},
                'flipkart': {'positive': 100, 'neutral': 40, 'negative': 15, 'reliability_score': 80},
                'alibaba': {'positive': 80, 'neutral': 35, 'negative': 20, 'reliability_score': 75},
                'croma': {'positive': 70, 'neutral': 30, 'negative': 15, 'reliability_score': 78}
            },
            'most_reliable_platform': 'amazon',
            'reliability_score': 85
        }
    
    return {
        'platform_scores': reliability_data,
        'most_reliable_platform': most_reliable_platform,
        'reliability_score': reliability_score
    }

def get_trending_products():
    # Get trending products based on search history and price history
    trending_products = []
    
    try:
        # Get products with most price history entries in the last week
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Group by product and count occurrences - using func.count and text for ORDER BY
        product_counts = db.session.query(
            PriceHistory.product_name,
            func.count(PriceHistory.id).label('count')
        ).filter(PriceHistory.timestamp >= one_week_ago)\
         .group_by(PriceHistory.product_name)\
         .order_by(text('count DESC'))\
         .limit(5).all()
        
        for product_name, count in product_counts:
            # Get the latest price for this product
            latest_price = PriceHistory.query.filter_by(product_name=product_name)\
                .order_by(PriceHistory.timestamp.desc()).first()
            
            if latest_price:
                trending_products.append({
                    'name': product_name,
                    'platform': latest_price.platform,
                    'price': latest_price.price,
                    'url': latest_price.url,
                    'trend_score': count
                })
    except Exception as e:
        logger.error(f"Error in get_trending_products: {str(e)}")
        logger.error(traceback.format_exc())
        # Return sample data on error
        trending_products = [
            {'name': 'iPhone 13', 'platform': 'amazon', 'price': 74999, 'url': '#', 'trend_score': 120},
            {'name': 'Samsung Galaxy S22', 'platform': 'flipkart', 'price': 65999, 'url': '#', 'trend_score': 100},
            {'name': 'MacBook Pro', 'platform': 'amazon', 'price': 129999, 'url': '#', 'trend_score': 95},
            {'name': 'OnePlus 10T', 'platform': 'croma', 'price': 45999, 'url': '#', 'trend_score': 85},
            {'name': 'iPad Air', 'platform': 'amazon', 'price': 54999, 'url': '#', 'trend_score': 80}
        ]
    
    return trending_products

# New route to set price alerts
@app.route('/set-alert', methods=['POST'])
@login_required
def set_alert():
    try:
        product_name = request.form.get('product_name')
        platform = request.form.get('platform')
        current_price = request.form.get('current_price')
        target_price = request.form.get('target_price')
        
        if not product_name or not platform or not current_price or not target_price:
            flash('All fields are required', 'danger')
            return redirect(url_for('profile'))
        
        # Convert prices to float
        try:
            current_price = float(current_price)
            target_price = float(target_price)
        except ValueError:
            flash('Invalid price values', 'danger')
            return redirect(url_for('profile'))
        
        # Create alert
        alert = PriceAlert(
            user_id=current_user.id,
            product_name=product_name,
            platform=platform,
            current_price=current_price,
            target_price=target_price,
            status='Active'
        )
        
        db.session.add(alert)
        db.session.commit()
        
        flash('Price alert set successfully!', 'success')
        return redirect(url_for('profile'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting price alert: {str(e)}")
        flash('Error setting price alert', 'danger')
        return redirect(url_for('profile'))

# New route to delete price alerts
@app.route('/delete-alert/<int:alert_id>', methods=['POST'])
@login_required
def delete_alert(alert_id):
    try:
        alert = PriceAlert.query.filter_by(id=alert_id, user_id=current_user.id).first()
        
        if not alert:
            flash('Alert not found', 'danger')
            return redirect(url_for('profile'))
        
        db.session.delete(alert)
        db.session.commit()
        
        flash('Alert deleted successfully', 'success')
        return redirect(url_for('profile'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting price alert: {str(e)}")
        flash('Error deleting price alert', 'danger')
        return redirect(url_for('profile'))

@app.route('/init-db')
def init_db():
    """Initialize the database (for development only)"""
    with app.app_context():
        db.create_all()
        
        # Create a test user if it doesn't exist
        admin = db.session.query(User).filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@pricewizard.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
        # Add some sample data
        if db.session.query(PriceHistory).count() == 0:
            platforms = ['amazon', 'flipkart', 'alibaba', 'croma']
            sample_products = [
                "iPhone 13 Pro Max",
                "Samsung Galaxy S21",
                "MacBook Pro 16-inch",
                "Sony PlayStation 5",
                "Nintendo Switch"
            ]
            
            for product in sample_products:
                base_price = random.randint(10000, 80000)
                
                for platform in platforms:
                    # Add price points for each product/platform
                    for i in range(10):
                        price_variation = random.uniform(0.9, 1.1)
                        price = base_price * price_variation
                        
                        timestamp = datetime.now() - timedelta(days=i)
                        
                        price_history = PriceHistory(
                            product_name=product,
                            platform=platform,
                            price=price,
                            url=f"https://www.{platform}.com/product/{product.lower().replace(' ', '-')}",
                            timestamp=timestamp
                        )
                        
                        db.session.add(price_history)
            
            db.session.commit()
            
    return "Database initialized with sample data"

@app.route('/reset-db')
def reset_db():
    """Reset the database (for development only)"""
    with app.app_context():
        db.drop_all()
        db.create_all()
    return "Database reset"

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
    os.makedirs('data/cache', exist_ok=True)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    logger.info("Starting Flask application on http://127.0.0.1:5000")
    app.run(debug=True)