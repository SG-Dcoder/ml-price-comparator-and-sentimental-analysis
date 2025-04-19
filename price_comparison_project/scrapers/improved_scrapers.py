import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os
from datetime import datetime

class ImprovedAmazonScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        }
        # Add cookies to appear more like a real browser
        self.cookies = {
            'session-id': '123456789',
            'session-token': 'abcdefghijklmnopqrstuvwxyz',
            'ubid-main': '123-4567890-1234567'
        }
    
    def search_product(self, query):
        print(f"Searching Amazon for: {query}")
        # Use a more realistic search URL
        search_query = query.replace(' ', '+')
        url = f'https://www.amazon.in/s?k={search_query}&ref=nb_sb_noss'
        
        try:
            # Add delay to avoid rate limiting
            time.sleep(2 + random.random() * 3)
            
            # Use session to maintain cookies
            session = requests.Session()
            
            # Make the request with headers and cookies
            response = session.get(url, headers=self.headers, cookies=self.cookies, timeout=10)
            
            print(f"Amazon response status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # For debugging - save the HTML to a file
                with open('amazon_debug.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                
                products = []
                
                # Try different product container selectors
                results = soup.select('div[data-component-type="s-search-result"]')
                print(f"Found {len(results)} raw results on Amazon")
                
                if not results:
                    # Try alternative selectors
                    results = soup.select('.s-result-item')
                    print(f"Using alternative selector, found {len(results)} results")
                
                for item in results[:10]:  # Limit to first 10 results
                    product = {}
                    
                    # Try to extract name
                    title_element = item.select_one('.a-size-medium.a-color-base.a-text-normal')
                    if not title_element:
                        title_element = item.select_one('.a-size-base-plus.a-color-base.a-text-normal')
                    if not title_element:
                        title_element = item.select_one('h2 a span')
                    
                    if title_element:
                        product['name'] = title_element.text.strip()
                    
                    # Try to extract price
                    price_element = item.select_one('.a-price .a-offscreen')
                    if not price_element:
                        price_element = item.select_one('.a-price-whole')
                    
                    if price_element:
                        price_text = price_element.text.replace('₹', '').replace(',', '').strip()
                        try:
                            # Extract only digits
                            price_text = ''.join(c for c in price_text if c.isdigit() or c == '.')
                            product['price'] = price_text
                        except:
                            continue
                    
                    # Try to extract URL
                    link_element = item.select_one('h2 a')
                    if not link_element:
                        link_element = item.select_one('.a-link-normal')
                    
                    if link_element and link_element.get('href'):
                        href = link_element.get('href')
                        if href.startswith('/'):
                            product['url'] = 'https://www.amazon.in' + href
                        else:
                            product['url'] = href
                    
                    # Try to extract rating
                    rating_element = item.select_one('.a-icon-alt')
                    if rating_element:
                        rating_text = rating_element.text
                        if 'out of 5 stars' in rating_text:
                            try:
                                product['rating'] = rating_text.split(' ')[0]
                            except:
                                pass
                    
                    if 'name' in product and 'price' in product and 'url' in product:
                        products.append(product)
                        print(f"Found product: {product['name'][:30]}... - ₹{product['price']}")
                
                return products
            else:
                print(f"Failed to fetch data from Amazon: {response.status_code}")
                print(f"Response content: {response.text[:200]}...")  # Print first 200 chars
                return []
        except Exception as e:
            print(f"Error during Amazon scraping: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def save_price_history(self, product_name, price, file_path):
        """Save product price history to JSON file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Load existing price history
        price_history = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    price_history = json.load(f)
            except Exception as e:
                print(f"Error loading price history: {str(e)}")
                price_history = []
        
        # Add new price point
        price_history.append({
            'product': product_name,
            'price': price,
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        
        # Save updated price history
        try:
            with open(file_path, 'w') as f:
                json.dump(price_history, f, indent=2)
            print(f"Price history saved for {product_name}")
        except Exception as e:
            print(f"Error saving price history: {str(e)}")

    def get_product_reviews(self, product_url):
        """Get product reviews (currently returns dummy data)"""
        print(f"Getting reviews for Amazon product: {product_url}")
        
        try:
            # In a real implementation, we would scrape actual reviews here
            # For now, return dummy data with some randomization
            positive = random.randint(15, 60)
            neutral = random.randint(5, 20)
            negative = random.randint(1, 15)
            total = positive + neutral + negative
            
            return {
                'positive': positive,
                'neutral': neutral,
                'negative': negative,
                'total_reviews': total,
                'reliability_score': random.randint(65, 95)
            }
        except Exception as e:
            print(f"Error getting reviews: {str(e)}")
            # Return fallback data
            return {
                'positive': 30,
                'neutral': 10,
                'negative': 5,
                'total_reviews': 45,
                'reliability_score': 75
            }

class ImprovedFlipkartScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        }
    
    def search_product(self, query):
        print(f"Searching Flipkart for: {query}")
        search_query = query.replace(' ', '%20')
        url = f'https://www.flipkart.com/search?q={search_query}&otracker=search&otracker1=search&marketplace=FLIPKART'
        
        try:
            # Add delay to avoid rate limiting
            time.sleep(2 + random.random() * 3)
            
            # Use session to maintain cookies
            session = requests.Session()
            
            # Make the request with headers
            response = session.get(url, headers=self.headers, timeout=10)
            
            print(f"Flipkart response status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # For debugging - save the HTML to a file
                with open('flipkart_debug.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                
                products = []
                
                # Try different product container selectors
                results = soup.select('div._1AtVbE')
                print(f"Found {len(results)} raw results on Flipkart")
                
                if not results:
                    # Try alternative selectors
                    results = soup.select('div._13oc-S')
                    print(f"Using alternative selector, found {len(results)} results")
                
                product_count = 0
                for item in results:
                    if product_count >= 10:  # Limit to first 10 results
                        break
                        
                    product = {}
                    
                    # Try to extract name
                    title_element = item.select_one('div._4rR01T')
                    if not title_element:
                        title_element = item.select_one('a.s1Q9rs')
                    if not title_element:
                        title_element = item.select_one('a.IRpwTa')
                    
                    if title_element:
                        product['name'] = title_element.text.strip()
                    
                    # Try to extract price
                    price_element = item.select_one('div._30jeq3')
                    if not price_element:
                        price_element = item.select_one('div._30jeq3._1_WHN1')
                    
                    if price_element:
                        price_text = price_element.text.replace('₹', '').replace(',', '').strip()
                        try:
                            # Extract only digits
                            price_text = ''.join(c for c in price_text if c.isdigit() or c == '.')
                            product['price'] = price_text
                        except:
                            continue
                    
                    # Try to extract URL
                    link_element = item.select_one('a._1fQZEK')
                    if not link_element:
                        link_element = item.select_one('a._2rpwqI')
                    if not link_element:
                        link_element = item.select_one('a.IRpwTa')
                    if not link_element:
                        link_element = item.select_one('a')  # Try any anchor tag
                    
                    if link_element and link_element.get('href'):
                        href = link_element.get('href')
                        if href.startswith('/'):
                            product['url'] = 'https://www.flipkart.com' + href
                        else:
                            product['url'] = href
                    
                    # Try to extract rating
                    rating_element = item.select_one('div._3LWZlK')
                    if rating_element:
                        product['rating'] = rating_element.text.strip()
                    
                    if 'name' in product and 'price' in product and 'url' in product:
                        products.append(product)
                        product_count += 1
                        print(f"Found product: {product['name'][:30]}... - ₹{product['price']}")
                
                return products
            else:
                print(f"Failed to fetch data from Flipkart: {response.status_code}")
                print(f"Response content: {response.text[:200]}...")  # Print first 200 chars
                return []
        except Exception as e:
            print(f"Error during Flipkart scraping: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def save_price_history(self, product_name, price, file_path):
        """Save product price history to JSON file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Load existing price history
        price_history = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    price_history = json.load(f)
            except Exception as e:
                print(f"Error loading price history: {str(e)}")
                price_history = []
        
        # Add new price point
        price_history.append({
            'product': product_name,
            'price': price,
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        
        # Save updated price history
        try:
            with open(file_path, 'w') as f:
                json.dump(price_history, f, indent=2)
            print(f"Price history saved for {product_name}")
        except Exception as e:
            print(f"Error saving price history: {str(e)}")

    def get_product_reviews(self, product_url):
        """Get product reviews (currently returns dummy data)"""
        print(f"Getting reviews for Flipkart product: {product_url}")
        
        try:
            # In a real implementation, we would scrape actual reviews here
            # For now, return dummy data with some randomization
            positive = random.randint(20, 55)
            neutral = random.randint(8, 25)
            negative = random.randint(3, 18)
            total = positive + neutral + negative
            
            return {
                'positive': positive,
                'neutral': neutral,
                'negative': negative,
                'total_reviews': total,
                'reliability_score': random.randint(60, 90)
            }
        except Exception as e:
            print(f"Error getting reviews: {str(e)}")
            # Return fallback data
            return {
                'positive': 25,
                'neutral': 15,
                'negative': 10,
                'total_reviews': 50,
                'reliability_score': 70
            }