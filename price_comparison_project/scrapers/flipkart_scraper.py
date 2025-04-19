import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

class FlipkartScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
    def search_product(self, query):
        search_query = query.replace(' ', '%20')
        url = f'https://www.flipkart.com/search?q={search_query}'
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                products = []
                results = soup.find_all('div', {'class': '_1AtVbE'})
                
                for item in results[:5]:  # Limit to first 5 results
                    product = {}
                    
                    # Extract product name
                    title_element = item.find('div', {'class': '_4rR01T'})
                    if not title_element:
                        title_element = item.find('a', {'class': 's1Q9rs'})
                    if title_element:
                        product['name'] = title_element.text.strip()
                    
                    # Extract price
                    price_element = item.find('div', {'class': '_30jeq3'})
                    if price_element:
                        # Remove ₹ symbol and commas
                        price_text = price_element.text.replace('₹', '').replace(',', '').strip()
                        product['price'] = price_text
                    
                    # Extract URL
                    link_element = item.find('a', {'class': '_1fQZEK'})
                    if not link_element:
                        link_element = item.find('a', {'class': '_2rpwqI'})
                    if link_element:
                        product['url'] = 'https://www.flipkart.com' + link_element.get('href')
                    
                    # Extract rating
                    rating_element = item.find('div', {'class': '_3LWZlK'})
                    if rating_element:
                        product['rating'] = rating_element.text.strip()
                    
                    if 'name' in product and 'price' in product and 'url' in product:
                        products.append(product)
                
                return products
            else:
                print(f"Failed to fetch data: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            return []
    
    def get_product_reviews(self, product_url, num_reviews=10):
        try:
            # Add /reviews to the product URL
            if '?' in product_url:
                review_url = product_url.split('?')[0] + '/reviews?' + product_url.split('?')[1]
            else:
                review_url = product_url + '/reviews'
                
            response = requests.get(review_url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                reviews = []
                review_elements = soup.find_all('div', {'class': 't-ZTKy'})
                
                for review in review_elements[:num_reviews]:
                    if review:
                        # Some reviews might be collapsed, try to get the full text
                        div_with_text = review.find('div')
                        if div_with_text:
                            reviews.append(div_with_text.text.strip())
                        else:
                            reviews.append(review.text.strip())
                
                return reviews
            else:
                print(f"Failed to fetch reviews: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching reviews: {str(e)}")
            return []
    
    def save_price_history(self, product_name, price, file_path='data/price_history/flipkart.json'):
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create a record with timestamp
            record = {
                'product': product_name,
                'price': price,
                'platform': 'Flipkart',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Load existing data or create new
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = []
            
            # Append new record
            data.append(record)
            
            # Save back to file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving price history: {str(e)}")
            return False