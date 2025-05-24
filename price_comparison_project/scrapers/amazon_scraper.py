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
            response = session.get(url, headers=self.headers, cookies=self.cookies, timeout=15)
            
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
                    
                    # Try to extract image URL
                    img_element = item.select_one('img.s-image')
                    if img_element and img_element.get('src'):
                        product['image_url'] = img_element.get('src')
                    
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
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Save updated price history
        try:
            with open(file_path, 'w') as f:
                json.dump(price_history, f, indent=2)
            print(f"Price history saved for {product_name}")
        except Exception as e:
            print(f"Error saving price history: {str(e)}")

    def get_product_reviews(self, product_url):
        """Get product reviews from Amazon"""
        print(f"Getting reviews for Amazon product: {product_url}")
        
        try:
            # Add delay to avoid rate limiting
            time.sleep(2 + random.random() * 3)
            
            # Use session to maintain cookies
            session = requests.Session()
            
            # Make the request with headers and cookies
            response = session.get(product_url, headers=self.headers, cookies=self.cookies, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find review section or link to reviews
                review_link_element = soup.select_one('a[data-hook="see-all-reviews-link-foot"]')
                
                if review_link_element and review_link_element.get('href'):
                    review_url = 'https://www.amazon.in' + review_link_element.get('href')
                    
                    # Fetch the reviews page
                    time.sleep(1 + random.random() * 2)
                    review_response = session.get(review_url, headers=self.headers, cookies=self.cookies, timeout=15)
                    
                    if review_response.status_code == 200:
                        review_soup = BeautifulSoup(review_response.content, 'html.parser')
                        
                        # Extract reviews
                        review_elements = review_soup.select('div[data-hook="review"]')
                        
                        positive = 0
                        neutral = 0
                        negative = 0
                        
                        for review in review_elements[:20]:  # Limit to 20 reviews
                            # Extract rating
                            rating_element = review.select_one('i[data-hook="review-star-rating"] span')
                            
                            if rating_element:
                                rating_text = rating_element.text
                                if 'out of 5 stars' in rating_text:
                                    try:
                                        rating = float(rating_text.split(' ')[0])
                                        if rating >= 4:
                                            positive += 1
                                        elif rating >= 3:
                                            neutral += 1
                                        else:
                                            negative += 1
                                    except:
                                        neutral += 1
                        
                        total = positive + neutral + negative
                        
                        if total > 0:
                            # Calculate reliability score based on reviews
                            reliability_score = (positive * 100 + neutral * 50) / (total * 100) * 100
                            reliability_score = min(100, max(0, reliability_score))
                            
                            return {
                                'positive': positive,
                                'neutral': neutral,
                                'negative': negative,
                                'total_reviews': total,
                                'reliability_score': round(reliability_score)
                            }
                
                # If we couldn't extract reviews, try to get the overall rating
                rating_element = soup.select_one('#acrPopover')
                if rating_element:
                    rating_text = rating_element.get('title', '')
                    if 'out of 5 stars' in rating_text:
                        try:
                            rating = float(rating_text.split(' ')[0])
                            # Generate synthetic review distribution based on overall rating
                            total_reviews = random.randint(20, 100)
                            if rating >= 4.5:
                                positive = int(total_reviews * 0.8)
                                neutral = int(total_reviews * 0.15)
                                negative = total_reviews - positive - neutral
                            elif rating >= 4.0:
                                positive = int(total_reviews * 0.7)
                                neutral = int(total_reviews * 0.2)
                                negative = total_reviews - positive - neutral
                            elif rating >= 3.5:
                                positive = int(total_reviews * 0.6)
                                neutral = int(total_reviews * 0.25)
                                negative = total_reviews - positive - neutral
                            elif rating >= 3.0:
                                positive = int(total_reviews * 0.5)
                                neutral = int(total_reviews * 0.3)
                                negative = total_reviews - positive - neutral
                            else:
                                positive = int(total_reviews * 0.3)
                                neutral = int(total_reviews * 0.3)
                                negative = total_reviews - positive - neutral
                            
                            reliability_score = (positive * 100 + neutral * 50) / (total_reviews * 100) * 100
                            
                            return {
                                'positive': positive,
                                'neutral': neutral,
                                'negative': negative,
                                'total_reviews': total_reviews,
                                'reliability_score': round(reliability_score),
                                'note': 'Based on overall rating'
                            }
                        except:
                            pass
            
            # If all else fails, return dummy data
            print("Falling back to dummy review data for Amazon")
            return self._generate_dummy_reviews()
            
        except Exception as e:
            print(f"Error getting Amazon reviews: {str(e)}")
            return self._generate_dummy_reviews()
        
    def _generate_dummy_reviews(self):
        """Generate dummy review data with some randomization"""
        positive = random.randint(15, 60)
        neutral = random.randint(5, 20)
        negative = random.randint(1, 15)
        total = positive + neutral + negative
        
        return {
            'positive': positive,
            'neutral': neutral,
            'negative': negative,
            'total_reviews': total,
            'reliability_score': random.randint(65, 95),
            'note': 'Dummy data'
        }