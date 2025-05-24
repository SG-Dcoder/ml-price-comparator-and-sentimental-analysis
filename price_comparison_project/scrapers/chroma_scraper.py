import requests
from bs4 import BeautifulSoup
import json
import random
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ChromaProductScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.base_url = "https://www.croma.com"
        self.search_url = "https://www.croma.com/search/?text="
    
    def search_product(self, query):
        """Search for products on Croma"""
        try:
            # Format query for URL
            search_query = query.replace(' ', '%20')
            search_url = f"{self.search_url}{search_query}"
            
            logger.info(f"Searching Croma for: {query} at URL: {search_url}")
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to get Croma search results. Status code: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract products from search results
            products = []
            product_cards = soup.select('.product-item')
            
            for card in product_cards[:5]:  # Get top 5 results
                try:
                    # Extract product details
                    name_elem = card.select_one('.product-title')
                    price_elem = card.select_one('.pdpPrice')
                    url_elem = card.select_one('a.product-title')
                    image_elem = card.select_one('img.product-img')
                    rating_elem = card.select_one('.rating-count')
                    
                    if not name_elem or not url_elem:
                        continue
                    
                    name = name_elem.text.strip()
                    
                    url = url_elem.get('href', '')
                    if url and not url.startswith('http'):
                        url = self.base_url + url
                    
                    price = "N/A"
                    if price_elem:
                        price_text = price_elem.text.strip()
                        # Extract numeric part of the price
                        import re
                        price_match = re.search(r'[\d,.]+', price_text)
                        if price_match:
                            price = price_match.group().replace(',', '')
                    
                    image_url = image_elem.get('src', '') if image_elem else ''
                    
                    rating = "N/A"
                    if rating_elem:
                        rating_text = rating_elem.text.strip()
                        rating_match = re.search(r'[\d.]+', rating_text)
                        if rating_match:
                            rating = rating_match.group()
                    
                    products.append({
                        'name': name,
                        'price': price,
                        'url': url,
                        'rating': rating,
                        'image_url': image_url
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting Croma product: {str(e)}")
                    continue
            
            logger.info(f"Found {len(products)} products on Croma")
            return products
            
        except Exception as e:
            logger.error(f"Error in Croma search: {str(e)}")
            return []
    
    def get_product_reviews(self, product_url):
        """Get product reviews from Croma"""
        try:
            response = requests.get(product_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to get Croma product page. Status code: {response.status_code}")
                return self._get_dummy_reviews()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to extract review data
            # This is a simplified approach - actual implementation would need to adapt to Croma's structure
            review_section = soup.select_one('.review-section')
            if not review_section:
                return self._get_dummy_reviews()
            
            # Try to find positive, neutral, and negative reviews
            # This is approximate since Croma might not categorize reviews this way
            all_reviews = review_section.select('.review-item')
            total_reviews = len(all_reviews)
            
            if total_reviews == 0:
                return self._get_dummy_reviews()
            
            # Count reviews by rating
            positive = 0
            neutral = 0
            negative = 0
            
            for review in all_reviews:
                rating_elem = review.select_one('.rating-value')
                if rating_elem:
                    try:
                        rating = float(rating_elem.text.strip())
                        if rating >= 4:
                            positive += 1
                        elif rating >= 3:
                            neutral += 1
                        else:
                            negative += 1
                    except:
                        # If can't parse rating, consider it neutral
                        neutral += 1
                else:
                    # If no rating element, consider it neutral
                    neutral += 1
            
            return {
                'positive': positive,
                'neutral': neutral,
                'negative': negative,
                'total_reviews': total_reviews,
                'reliability_score': self._calculate_reliability_score(positive, neutral, negative),
                'is_real_data': True
            }
        except Exception as e:
            logger.error(f"Error getting Croma reviews: {str(e)}")
            return self._get_dummy_reviews()
    
    def _get_dummy_reviews(self):
        """Generate dummy review data"""
        positive = random.randint(20, 50)
        neutral = random.randint(5, 20)
        negative = random.randint(2, 15)
        total_reviews = positive + neutral + negative
        
        return {
            'positive': positive,
            'neutral': neutral,
            'negative': negative,
            'total_reviews': total_reviews,
            'reliability_score': self._calculate_reliability_score(positive, neutral, negative),
            'is_real_data': False
        }
    
    def _calculate_reliability_score(self, positive, neutral, negative):
        """Calculate reliability score based on sentiment distribution"""
        total = positive + neutral + negative
        if total == 0:
            return 0
        
        reliability_score = (positive * 100 + neutral * 50) / (total * 100) * 100
        return round(max(0, min(100, reliability_score)))
    
    def save_price_history(self, product_name, price, file_path='data/price_history/croma.json'):
        """Save price data to JSON file for historical tracking"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Read existing data
            existing_data = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
            
            # Add new price data
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_data = {
                'product': product_name,
                'price': str(price),
                'timestamp': timestamp
            }
            
            existing_data.append(new_data)
            
            # Write back to file
            with open(file_path, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
            logger.info(f"Saved Croma price history for {product_name}")
            
        except Exception as e:
            logger.error(f"Error saving Croma price history: {str(e)}")