import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

class AmazonScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
    def search_product(self, query):
        search_query = query.replace(' ', '+')
        url = f'https://www.amazon.in/s?k={search_query}'
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                products = []
                results = soup.find_all('div', {'data-component-type': 's-search-result'})
                
                for item in results[:5]:  # Limit to first 5 results
                    product = {}
                    
                    # Extract product name
                    title_element = item.find('span', {'class': 'a-size-medium'})
                    if not title_element:
                        title_element = item.find('span', {'class': 'a-size-base-plus'})
                    if title_element:
                        product['name'] = title_element.text.strip()
                    
                    # Extract price
                    price_element = item.find('span', {'class': 'a-price-whole'})
                    if price_element:
                        product['price'] = price_element.text.replace(',', '').strip()
                    
                    # Extract URL
                    link_element = item.find('a', {'class': 'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'})
                    if link_element:
                        product['url'] = 'https://www.amazon.in' + link_element.get('href')
                    
                    # Extract rating
                    rating_element = item.find('span', {'class': 'a-icon-alt'})
                    if rating_element and 'out of 5 stars' in rating_element.text:
                        product['rating'] = rating_element.text.split(' ')[0]
                    
                    if 'name' in product and 'price' in product:
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
            # Extract ASIN from URL
            asin = None
            if "/dp/" in product_url:
                asin = product_url.split('/dp/')[1].split('/')[0]
            elif "/gp/product/" in product_url:
                asin = product_url.split('/gp/product/')[1].split('/')[0]
            
            if not asin:
                return []
                
            review_url = f"https://www.amazon.in/product-reviews/{asin}"
            response = requests.get(review_url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                reviews = []
                review_elements = soup.find_all('span', {'data-hook': 'review-body'})
                
                for review in review_elements[:num_reviews]:
                    if review:
                        reviews.append(review.text.strip())
                
                return reviews
            else:
                print(f"Failed to fetch reviews: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching reviews: {str(e)}")
            return []
    
    def save_price_history(self, product_name, price, file_path='data/price_history/amazon.json'):
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create a record with timestamp
            record = {
                'product': product_name,
                'price': price,
                'platform': 'Amazon',
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