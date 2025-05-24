# import requests
# from bs4 import BeautifulSoup
# import json
# import random
# import logging
# import re
# from datetime import datetime
# import os

# logger = logging.getLogger(__name__)

# class MyntraProductScraper:
#     def __init__(self):
#         self.headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#             'Accept-Language': 'en-US,en;q=0.9',
#         }
#         self.base_url = "https://www.myntra.com"
#         self.search_url = "https://www.myntra.com/search?q="
    
#     def search_product(self, query):
#         """Search for products on Myntra"""
#         try:
#             # Process query to understand what we're looking for
#             query_info = self._process_search_query(query)
            
#             # Format query for URL
#             search_query = query.replace(' ', '%20')
#             search_url = f"{self.search_url}{search_query}"
            
#             logger.info(f"Searching Myntra for: {query} at URL: {search_url}")
            
#             response = requests.get(search_url, headers=self.headers, timeout=10)
#             if response.status_code != 200:
#                 logger.error(f"Failed to get Myntra search results. Status code: {response.status_code}")
#                 return []
            
#             # Myntra uses JavaScript to load products, so we might need to simulate browser behavior
#             # For now, we'll try to extract what we can from the initial HTML
#             soup = BeautifulSoup(response.content, 'html.parser')
            
#             # Extract products from search results
#             products = []
#             product_cards = soup.select('.product-base')
            
#             for card in product_cards[:10]:  # Get top 10 results for better filtering
#                 try:
#                     # Extract product details
#                     name_elem = card.select_one('.product-product')
#                     brand_elem = card.select_one('.product-brand')
#                     price_elem = card.select_one('.product-price')
#                     url_elem = card.select_one('a')
#                     image_elem = card.select_one('img.product-image')
                    
#                     # Combine brand and product name if both exist
#                     name = ""
#                     if brand_elem:
#                         name += brand_elem.text.strip() + " "
#                     if name_elem:
#                         name += name_elem.text.strip()
                    
#                     # If we couldn't get a proper name, skip this product
#                     if not name:
#                         continue
                    
#                     url = url_elem.get('href', '') if url_elem else ''
#                     if url and not url.startswith('http'):
#                         url = self.base_url + url
                    
#                     price = "N/A"
#                     if price_elem:
#                         price_text = price_elem.text.strip()
#                         # Extract numeric part of the price
#                         price_match = re.search(r'[\d,.]+', price_text)
#                         if price_match:
#                             price = price_match.group().replace(',', '')
                    
#                     image_url = image_elem.get('src', '') if image_elem else ''
                    
#                     # Myntra doesn't show ratings directly in search results
#                     rating = "N/A"
                    
#                     products.append({
#                         'name': name,
#                         'price': price,
#                         'url': url,
#                         'rating': rating,
#                         'image_url': image_url
#                     })
                    
#                 except Exception as e:
#                     logger.error(f"Error extracting Myntra product: {str(e)}")
#                     continue
            
#             # If we couldn't extract products, it might be due to JavaScript rendering
#             # Return dummy products as a fallback
#             if not products:
#                 products = self._get_dummy_products(query)
#                 return products
            
#             # Apply stricter filtering for electronics on Myntra
#             if query_info["product_type"] in ["phone", "laptop", "tablet", "tv"]:
#                 # Myntra primarily sells fashion items, so for electronics searches,
#                 # we need to be very strict about filtering
#                 filtered_results = []
#                 for product in products:
#                     product_name_lower = product['name'].lower()
                    
#                     # Skip any product that doesn't match the main product type
#                     if query_info["product_type"] == "phone" and not any(keyword in product_name_lower for keyword in ["phone", "mobile", "smartphone", "iphone"]):
#                         continue
                        
#                     # Skip products that are clearly accessories
#                     accessory_keywords = [
#                         'case', 'cover', 'screen protector', 'screen guard', 'charger', 'cable', 
#                         'adapter', 'skin', 'stand', 'holder', 'mount', 'dock', 'pouch', 'bag',
#                         'tempered glass', 'protective', 'shell', 'bumper', 'wallet', 'essentials'
#                     ]
                    
#                     if any(keyword in product_name_lower for keyword in accessory_keywords):
#                         continue
                    
#                     # For phones, require specific model name or number
#                     if query_info["product_type"] == "phone" and query_info["model_specs"]:
#                         if not any(spec.lower() in product_name_lower for spec in query_info["model_specs"]):
#                             continue
                    
#                     # For brand-specific searches, require the brand name
#                     if query_info["brand"] and query_info["brand"] not in product_name_lower:
#                         continue
                    
#                     filtered_results.append(product)
                
#                 # If we have filtered results, use them; otherwise fall back to dummy products
#                 if filtered_results:
#                     logger.info(f"Found {len(filtered_results)} filtered products on Myntra")
#                     return filtered_results
#                 else:
#                     logger.info("No matching electronics products found on Myntra, using dummy data")
#                     return self._get_electronics_dummy_products(query, query_info)
#             else:
#                 # For fashion items, use standard results
#                 logger.info(f"Found {len(products)} products on Myntra")
#                 return products
            
#         except Exception as e:
#             logger.error(f"Error in Myntra search: {str(e)}")
#             return self._get_dummy_products(query)
    
#     def _process_search_query(self, query):
#         """Extract product type and key attributes from search query"""
#         # Convert to lowercase for easier matching
#         query_lower = query.lower()
        
#         # Extract product type (phone, laptop, etc.)
#         product_types = {
#             "phone": ["iphone", "samsung", "galaxy", "pixel", "xiaomi", "redmi", "oneplus", "smartphone", "mobile"],
#             "laptop": ["macbook", "laptop", "notebook", "thinkpad", "zenbook", "xps"],
#             "tablet": ["ipad", "tab", "tablet", "galaxy tab"],
#             "watch": ["watch", "smartwatch", "apple watch", "galaxy watch"],
#             "headphone": ["airpods", "headphone", "earphone", "earbuds", "headset"],
#             "tv": ["tv", "television", "smart tv", "led tv", "oled"]
#         }
        
#         identified_type = None
#         for product_type, keywords in product_types.items():
#             if any(keyword in query_lower for keyword in keywords):
#                 identified_type = product_type
#                 break
        
#         # Extract brand
#         brands = ["apple", "samsung", "google", "xiaomi", "oneplus", "sony", "lg", "hp", "dell", "lenovo"]
#         identified_brand = None
#         for brand in brands:
#             if brand in query_lower:
#                 identified_brand = brand
#                 break
        
#         # Extract model and specifications
#         model_specs = []
        
#         # Look for model numbers/names (e.g., "15 Pro", "S21", "Air")
#         model_patterns = [
#             r'(\d+)\s*(pro|air|max|ultra|plus|\+)',  # 15 Pro, 13 Air, etc.
#             r'(s|note|tab)\s*(\d+)',  # S21, Note 20, etc.
#             r'(m\d+)',  # M1, M2 chip
#         ]
        
#         for pattern in model_patterns:
#             matches = re.findall(pattern, query_lower)
#             if matches:
#                 for match in matches:
#                     if isinstance(match, tuple):
#                         model_specs.append(''.join(match).strip())
#                     else:
#                         model_specs.append(match.strip())
        
#         # Look for storage capacity
#         storage_pattern = r'(\d+)\s*(gb|tb)'
#         storage_matches = re.findall(storage_pattern, query_lower)
#         if storage_matches:
#             for match in storage_matches:
#                 model_specs.append(''.join(match).strip())
        
#         return {
#             "product_type": identified_type,
#             "brand": identified_brand,
#             "model_specs": model_specs,
#             "original_query": query
#         }
    
#     def _get_dummy_products(self, query):
#         """Generate dummy products when scraping fails"""
#         logger.info(f"Using dummy data for Myntra")
        
#         base_price = random.randint(1000, 5000)
        
#         products = [
#             {
#                 'name': f'Myntra Premium {query.title()} Collection',
#                 'price': str(base_price),
#                 'url': f'https://www.myntra.com/product/dummy1',
#                 'rating': '4.2',
#                 'image_url': f'https://via.placeholder.com/200x200?text=Myntra+{query}'
#             },
#             {
#                 'name': f'Myntra {query.title()} Essentials',
#                 'price': str(int(base_price * 0.8)),
#                 'url': f'https://www.myntra.com/product/dummy2',
#                 'rating': '4.0',
#                 'image_url': f'https://via.placeholder.com/200x200?text=Myntra+Essentials'
#             },
#             {
#                 'name': f'Myntra {query.title()} Pro',
#                 'price': str(int(base_price * 1.2)),
#                 'url': f'https://www.myntra.com/product/dummy3',
#                 'rating': '4.5',
#                 'image_url': f'https://via.placeholder.com/200x200?text=Myntra+Pro'
#             }
#         ]
#         return products
    
#     def _get_electronics_dummy_products(self, query, query_info):
#         """Generate more realistic dummy products for electronics"""
#         logger.info(f"Using electronics dummy data for Myntra")
        
#         base_price = random.randint(30000, 80000) if query_info["product_type"] in ["phone", "laptop"] else random.randint(5000, 15000)
#         brand = query_info["brand"].title() if query_info["brand"] else "Premium"
#         model_spec = query_info["model_specs"][0] if query_info["model_specs"] else ""
        
#         products = []
        
#         if query_info["product_type"] == "phone":
#             products = [
#                 {
#                     'name': f'{brand} {query_info["product_type"].title()} {model_spec}',
#                     'price': str(base_price),
#                     'url': f'https://www.myntra.com/product/dummy-phone',
#                     'rating': '4.5',
#                     'image_url': f'https://via.placeholder.com/200x200?text={brand}+Phone'
#                 }
#             ]
#         elif query_info["product_type"] == "laptop":
#             products = [
#                 {
#                     'name': f'{brand} {query_info["product_type"].title()} {model_spec}',
#                     'price': str(base_price),
#                     'url': f'https://www.myntra.com/product/dummy-laptop',
#                     'rating': '4.3',
#                     'image_url': f'https://via.placeholder.com/200x200?text={brand}+Laptop'
#                 }
#             ]
#         else:
#             products = [
#                 {
#                     'name': f'{brand} {query_info["product_type"].title()} {model_spec}',
#                     'price': str(base_price),
#                     'url': f'https://www.myntra.com/product/dummy-device',
#                     'rating': '4.2',
#                     'image_url': f'https://via.placeholder.com/200x200?text={brand}+Device'
#                 }
#             ]
            
#         return products
    
#     def get_product_reviews(self, product_url):
#         """Get product reviews from Myntra"""
#         # Myntra doesn't have easily accessible reviews like Amazon/Flipkart
#         # Return dummy review data
#         return self._get_dummy_reviews()
    
#     def _get_dummy_reviews(self):
#         """Generate dummy review data"""
#         positive = random.randint(25, 60)
#         neutral = random.randint(10, 25)
#         negative = random.randint(3, 15)
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
    
#     def save_price_history(self, product_name, price, file_path='data/price_history/myntra.json'):
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
                
#             logger.info(f"Saved Myntra price history for {product_name}")
            
#         except Exception as e:
#             logger.error(f"Error saving Myntra price history: {str(e)}")