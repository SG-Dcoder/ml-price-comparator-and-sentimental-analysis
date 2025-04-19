import requests
from bs4 import BeautifulSoup
import json
import time
import random
import os
import re
from datetime import datetime

class ImprovedFlipkartScraper:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        ]
        
    def _get_headers(self):
        """Get random headers to avoid detection"""
        user_agent = random.choice(self.user_agents)
        return {
            'User-Agent': user_agent,
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Referer': 'https://www.google.com/'
        }
        
    def create_realistic_dummy_products(self, query, amazon_products=None):
        """Create realistic dummy products based on Amazon products if available"""
        print(f"Creating realistic dummy Flipkart products for: {query}")
        
        # If we have Amazon products, create similar Flipkart products with slight variations
        if amazon_products and len(amazon_products) > 0:
            flipkart_products = []
            
            for amazon_product in amazon_products[:5]:  # Use up to 5 Amazon products as templates
                try:
                    # Extract base name and modify it
                    name = amazon_product.get('name', f"Flipkart {query}")
                    if 'Amazon' in name:
                        name = name.replace('Amazon', 'Flipkart')
                    
                    # Get price and adjust it slightly
                    price = float(amazon_product.get('price', '50000'))
                    price_adjustment = random.uniform(0.9, 1.1)  # 10% up or down
                    adjusted_price = str(int(price * price_adjustment))
                    
                    # Create a Flipkart product based on the Amazon one
                    flipkart_product = {
                        'name': name,
                        'price': adjusted_price,
                        'url': f'https://www.flipkart.com/search?q={query.replace(" ", "+")}',
                        'rating': str(round(float(amazon_product.get('rating', '4.0')) * random.uniform(0.9, 1.1), 1))
                    }
                    
                    flipkart_products.append(flipkart_product)
                except Exception as e:
                    print(f"Error creating dummy product: {str(e)}")
            
            # Add a few more unique products
            base_price = random.randint(30000, 80000)
            
            additional_products = [
                {
                    'name': f'Flipkart {query} Pro Max',
                    'price': str(base_price),
                    'url': f'https://www.flipkart.com/search?q={query.replace(" ", "+")}',
                    'rating': '4.3'
                },
                {
                    'name': f'Flipkart {query} Ultra',
                    'price': str(int(base_price * 1.2)),
                    'url': f'https://www.flipkart.com/search?q={query.replace(" ", "+")}',
                    'rating': '4.5'
                }
            ]
            
            flipkart_products.extend(additional_products)
            return flipkart_products
        
        # If no Amazon products, create generic dummy products
        base_price = random.randint(30000, 80000)
        
        products = [
            {
                'name': f'Flipkart {query} Pro Max',
                'price': str(base_price),
                'url': f'https://www.flipkart.com/search?q={query.replace(" ", "+")}',
                'rating': '4.3'
            },
            {
                'name': f'Flipkart {query} Standard Edition',
                'price': str(int(base_price * 0.8)),
                'url': f'https://www.flipkart.com/search?q={query.replace(" ", "+")}',
                'rating': '4.1'
            },
            {
                'name': f'Flipkart {query} Lite',
                'price': str(int(base_price * 0.6)),
                'url': f'https://www.flipkart.com/search?q={query.replace(" ", "+")}',
                'rating': '4.0'
            },
            {
                'name': f'Flipkart {query} Ultra Premium',
                'price': str(int(base_price * 1.2)),
                'url': f'https://www.flipkart.com/search?q={query.replace(" ", "+")}',
                'rating': '4.7'
            },
            {
                'name': f'Flipkart {query} Mini',
                'price': str(int(base_price * 0.4)),
                'url': f'https://www.flipkart.com/search?q={query.replace(" ", "+")}',
                'rating': '3.9'
            }
        ]
        return products

    def search_product(self, query, amazon_products=None):
        """Search for products on Flipkart, falling back to realistic dummy data"""
        print(f"Searching Flipkart for: {query}")
        
        # Try to fetch real data with multiple retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # For smartphones, try a more specific URL
                if 'phone' in query.lower() or 'mobile' in query.lower() or 'smartphone' in query.lower():
                    search_query = query.replace(' ', '+')
                    url = f'https://www.flipkart.com/mobiles/pr?sid=tyy%2C4io&q={search_query}'
                else:
                    search_query = query.replace(' ', '+')
                    url = f'https://www.flipkart.com/search?q={search_query}'
                
                # Add longer delay to avoid rate limiting
                delay = 3 + random.random() * 5
                print(f"Waiting {delay:.1f} seconds before request (attempt {attempt+1}/{max_retries})...")
                time.sleep(delay)
                
                # Use session to maintain cookies
                session = requests.Session()
                
                # Get random headers
                headers = self._get_headers()
                
                # Make the request with headers
                response = session.get(url, headers=headers, timeout=15)
                
                print(f"Flipkart response status: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # For debugging - save the HTML to a file
                    with open('flipkart_debug.html', 'w', encoding='utf-8') as f:
                        f.write(soup.prettify())
                    
                    # Try to extract products
                    products = self._extract_products(soup)
                    
                    if products:
                        print(f"Successfully extracted {len(products)} products from Flipkart")
                        return products[:10]  # Limit to first 10 products
                    else:
                        print("No products found in the HTML, trying again...")
                        continue
                elif response.status_code == 429:
                    print(f"Rate limited by Flipkart (429). Waiting longer before retry...")
                    time.sleep(10 + random.random() * 10)  # Wait 10-20 seconds
                    continue
                else:
                    print(f"Failed to fetch data from Flipkart: {response.status_code}")
                    continue
            except Exception as e:
                print(f"Error during Flipkart scraping (attempt {attempt+1}): {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(5)  # Wait before retry
        
        # If all attempts failed, use dummy data
        print("All scraping attempts failed, using realistic dummy data")
        return self.create_realistic_dummy_products(query, amazon_products)
    
    def _extract_products(self, soup):
        """Extract products from Flipkart HTML"""
        products = []
        
        # Try to find product cards - look for common patterns in Flipkart's HTML
        # Pattern 1: Look for product cards with images and prices
        product_cards = soup.select('div._2kHMtA, div._4ddWXP, div._1xHGtK, div._1AtVbE')
        
        if not product_cards:
            # Try alternative selectors
            product_cards = soup.select('div[style*="box-shadow"]')
        
        if not product_cards:
            # Try another approach - find all divs with links and prices
            product_cards = []
            price_elements = soup.select('div._30jeq3')
            for price_el in price_elements:
                # Go up a few levels to find the product container
                parent = price_el.parent
                for _ in range(3):
                    if parent and parent.name == 'div':
                        product_cards.append(parent)
                        break
                    parent = parent.parent if parent else None
        
        print(f"Found {len(product_cards)} potential product cards")
        
        # Process each product card
        for card in product_cards:
            product = {}
            
            # Try to extract name
            name_element = card.select_one('div._4rR01T, a.s1Q9rs, a.IRpwTa, div._2B099V, a[title]')
            if name_element:
                if name_element.has_attr('title'):
                    product['name'] = name_element['title']
                else:
                    product['name'] = name_element.text.strip()
            
            # Try to extract price
            price_element = card.select_one('div._30jeq3, div._30jeq3._1_WHN1')
            if price_element:
                price_text = price_element.text.replace('₹', '').replace(',', '').strip()
                try:
                    # Extract only digits
                    price_text = ''.join(c for c in price_text if c.isdigit() or c == '.')
                    product['price'] = price_text
                except:
                    continue
            
            # Try to extract URL
            link_element = card.select_one('a[href]')
            if link_element and link_element.get('href'):
                href = link_element.get('href')
                if href.startswith('/'):
                    product['url'] = 'https://www.flipkart.com' + href
                else:
                    product['url'] = href
            
            # Try to extract rating
            rating_element = card.select_one('div._3LWZlK, span._1lRcqv, div._3Ay6Sb span')
            if rating_element:
                rating_text = rating_element.text.strip()
                if rating_text:
                    # Try to extract just the number
                    rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                    if rating_match:
                        product['rating'] = rating_match.group(1)
                    else:
                        product['rating'] = rating_text
            
            # Only add product if we have the essential fields
            if 'name' in product and 'price' in product and 'url' in product:
                # Check if it's not just a category link
                if not ('Mobiles & Accessories' == product['name'] or 'Electronics' == product['name']):
                    products.append(product)
                    print(f"Found product: {product['name'][:30]}... - ₹{product['price']}")
        
        return products

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