import requests
from bs4 import BeautifulSoup
import json
import random
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class AlibabaProductScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.base_url = "https://www.alibaba.com/trade/search"
    
    def search_product(self, query):
        """Search for products on Alibaba"""
        try:
            # Format query for URL
            search_query = query.replace(' ', '+')
            search_url = f"{self.base_url}?fsb=y&IndexArea=product_en&CatId=&SearchText={search_query}"
            
            logger.info(f"Searching Alibaba for: {query} at URL: {search_url}")
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to get Alibaba search results. Status code: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract products from search results
            products = []
            product_cards = soup.select('.list-no-v2-main')
            
            for card in product_cards[:5]:  # Get top 5 results
                try:
                    # Extract product details
                    name_elem = card.select_one('.elements-title-normal__content')
                    price_elem = card.select_one('.elements-offer-price-normal__price')
                    url_elem = card.select_one('a.elements-title-normal')
                    image_elem = card.select_one('img.J-img-switcher-target')
                    
                    if not name_elem or not url_elem:
                        continue
                    
                    name = name_elem.text.strip()
                    url = url_elem.get('href', '')
                    if url and not url.startswith('http'):
                        url = 'https:' + url if url.startswith('//') else 'https://www.alibaba.com' + url
                    
                    # Price might be in a range or require minimum order
                    price = "N/A"
                    if price_elem:
                        price_text = price_elem.text.strip()
                        # Extract numeric part of the price
                        import re
                        price_match = re.search(r'[\d,.]+', price_text)
                        if price_match:
                            # Convert to INR (approximate conversion)
                            try:
                                price_value = float(price_match.group().replace(',', ''))
                                # Assuming price is in USD, convert to INR (approximate rate)
                                price = str(int(price_value * 83))  # 1 USD ≈ 83 INR
                            except:
                                pass
                    
                    image_url = image_elem.get('src', '') if image_elem else ''
                    if image_url and not image_url.startswith('http'):
                        image_url = 'https:' + image_url if image_url.startswith('//') else image_url
                    
                    # Rating is often not available on Alibaba, use placeholder
                    rating = "N/A"
                    
                    products.append({
                        'name': name,
                        'price': price,
                        'url': url,
                        'rating': rating,
                        'image_url': image_url
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting Alibaba product: {str(e)}")
                    continue
            
            logger.info(f"Found {len(products)} products on Alibaba")
            return products
            
        except Exception as e:
            logger.error(f"Error in Alibaba search: {str(e)}")
            return []
    
    def get_product_reviews(self, product_url):
        """Get product reviews from Alibaba (limited functionality)"""
        try:
            # Alibaba doesn't have easily accessible reviews like Amazon/Flipkart
            # Return dummy review data
            positive = random.randint(15, 40)
            neutral = random.randint(5, 15)
            negative = random.randint(2, 10)
            total_reviews = positive + neutral + negative
            
            return {
                'positive': positive,
                'neutral': neutral,
                'negative': negative,
                'total_reviews': total_reviews,
                'reliability_score': self._calculate_reliability_score(positive, neutral, negative),
                'is_real_data': False
            }
        except Exception as e:
            logger.error(f"Error getting Alibaba reviews: {str(e)}")
            return {
                'positive': 0,
                'neutral': 0,
                'negative': 0,
                'total_reviews': 0,
                'reliability_score': 0,
                'is_real_data': False
            }
    
    def _calculate_reliability_score(self, positive, neutral, negative):
        """Calculate reliability score based on sentiment distribution"""
        total = positive + neutral + negative
        if total == 0:
            return 0
        
        reliability_score = (positive * 100 + neutral * 50) / (total * 100) * 100
        return round(max(0, min(100, reliability_score)))
    
    def save_price_history(self, product_name, price, file_path='data/price_history/alibaba.json'):
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
                
            logger.info(f"Saved Alibaba price history for {product_name}")
            
        except Exception as e:
            logger.error(f"Error saving Alibaba price history: {str(e)}")