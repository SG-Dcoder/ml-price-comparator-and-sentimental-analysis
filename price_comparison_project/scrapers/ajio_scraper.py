# import requests
# from bs4 import BeautifulSoup
# import json
# import random
# import logging
# from datetime import datetime
# import os

# logger = logging.getLogger(__name__)

# class AjioProductScraper:
#     def __init__(self):
#         self.headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#             'Accept-Language': 'en-US,en;q=0.9',
#         }
#         self.base_url = "https://www.ajio.com"
#         self.search_url = "https://www.ajio.com/search/?text="
    
#     def search_product(self, query):
#         """Search for products on Ajio"""
#         try:
#             # Format query for URL
#             search_query = query.replace(' ', '%20')
#             search_url = f"{self.search_url}{search_query}"
            
#             logger.info(f"Searching Ajio for: {query} at URL: {search_url}")
            
#             response = requests.get(search_url, headers=self.headers, timeout=10)
#             if response.status_code != 200:
#                 logger.error(f"Failed to get Ajio search results. Status code: {response.status_code}")
#                 return []
            
#             # Ajio uses JavaScript to load products, so we might need to simulate browser behavior
#             # For now, we'll try to extract what we can from the initial HTML
#             soup = BeautifulSoup(response.content, 'html.parser')
            
#             # Extract products from search results
#             products = []
#             product_cards = soup.select('.item')
            
#             for card in product_cards[:5]:  # Get top 5 results
#                 try:
#                     # Extract product details
#                     name_elem = card.select_one('.nameCls')
#                     price_elem = card.select_one('.price')
#                     url_elem = card.select_one('a')
#                     image_elem = card.select_one('img.rilrtl-lazy-img')
                    
#                     if not name_elem or not url_elem:
#                         continue
                    
#                     name = name_elem.text.strip()
                    
#                     url = url_elem.get('href', '')
#                     if url and not url.startswith('http'):
#                         url = self.base_url + url
                    
#                     price = "N/A"
#                     if price_elem:
#                         price_text = price_elem.text.strip()
#                         # Extract numeric part of the price
#                         import re
#                         price_match = re.search(r'[\d,.]+', price_text)
#                         if price_match:
#                             price = price_match.group().replace(',', '')
                    
#                     image_url = image_elem.get('src', '') if image_elem else ''
#                     if not image_url and image_elem:
#                         image_url = image_elem.get('data-src', '')
                    
#                     # Ajio doesn't show ratings directly in search results
#                     rating = "N/A"
                    
#                     products.append({
#                         'name': name,
#                         'price': price,
#                         'url': url,
#                         'rating': rating,
#                         'image_url': image_url
#                     })
                    
#                 except Exception as e:
#                     logger.error(f"Error extracting Ajio product: {str(e)}")
#                     continue
            
#             # If we couldn't extract products, it might be due to JavaScript rendering
#             # Return dummy products as a fallback
#             if not products:
#                 products = self._get_dummy_products(query)
            
#             logger.info(f"Found {len(products)} products on Ajio")
#             return products
            
#         except Exception as e:
#             logger.error(f"Error in Ajio search: {str(e)}")
#             return self._get_dummy_products(query)
    
#     def _get_dummy_products(self, query):
#         """Generate dummy products when scraping fails"""
#         logger.info(f"Using dummy data for Ajio")
        
#         base_price = random.randint(1000, 5000)
        
#         products = [
#             {
#                 'name': f'Ajio Premium {query.title()} Collection',
#                 'price': str(base_price),
#                 'url': f'https://www.ajio.com/product/dummy1',
#                 'rating': '4.1',
#                 'image_url': f'https://via.placeholder.com/200x200?text=Ajio+{query}'
#             },
#             {
#                 'name': f'Ajio {query.title()} Essentials',
#                 'price': str(int(base_price * 0.8)),
#                 'url': f'https://www.ajio.com/product/dummy2',
#                 'rating': '3.9',
#                 'image_url': f'https://via.placeholder.com/200x200?text=Ajio+Essentials'
#             },
#             {
#                 'name': f'Ajio {query.title()} Pro',
#                 'price': str(int(base_price * 1.2)),
#                 'url': f'https://www.ajio.com/product/dummy3',
#                 'rating': '4.3',
#                 'image_url': f'https://via.placeholder.com/200x200?text=Ajio+Pro'
#             }
#         ]
#         return products
    
#     def get_product_reviews(self, product_url):
#         """Get product reviews from Ajio"""
#         # Ajio doesn't have easily accessible reviews like Amazon/Flipkart
#         # Return dummy review data
#         return self._get_dummy_reviews()
    
#     def _get_dummy_reviews(self):
#         """Generate dummy review data"""
#         positive = random.randint(20, 55)
#         neutral = random.randint(8, 20)
#         negative = random.randint(2, 12)
#         total_reviews = positive + neutral + negative
        
#         return {
#             'positive': positive,
#             'neutral': neutral,
#             'negative': negative,
#             'total_reviews': total_reviews,
#             'reliability_score': self._calculate_reliability_score(positive, neutral, negative),
#             'is_real_data': False
#         }
    
#     def _calculate_reliability_score(self, positive, neutral, negative):
#         """Calculate reliability score based on sentiment distribution"""
#         total = positive + neutral + negative
#         if total == 0:
#             return 0
        
#         reliability_score = (positive * 100 + neutral * 50) / (total * 100) * 100
#         return round(max(0, min(100, reliability_score)))
    
#     def save_price_history(self, product_name, price, file_path='data/price_history/ajio.json'):
#         """Save price data to JSON file for historical tracking"""
#         try:
#             # Create directory if it doesn't exist
#             os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
#             # Read existing data
#             existing_data = []
#             if os.path.exists(file_path):
#                 try:
#                     with open(file_path, 'r') as f:
#                         existing_data = json.load(f)
#                 except json.JSONDecodeError:
#                     existing_data = []
            
#             # Add new price data
#             timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#             new_data = {
#                 'product': product_name,
#                 'price': str(price),
#                 'timestamp': timestamp
#             }
            
#             existing_data.append(new_data)
            
#             # Write back to file
#             with open(file_path, 'w') as f:
#                 json.dump(existing_data, f, indent=2)
                
#             logger.info(f"Saved Ajio price history for {product_name}")
            
#         except Exception as e:
#             logger.error(f"Error saving Ajio price history: {str(e)}")