# test_flipkart_with_retry.py
from scrapers.flipkart_improved_scraper import ImprovedFlipkartScraper
from scrapers.improved_scrapers import ImprovedAmazonScraper
import json

amazon_scraper = ImprovedAmazonScraper()
flipkart_scraper = ImprovedFlipkartScraper()

query = "smartphone"
print(f"Testing improved Flipkart scraper with retry for: {query}")

# First get Amazon products for reference
amazon_products = amazon_scraper.search_product(query)
print(f"Found {len(amazon_products)} Amazon products for reference")

# Then try Flipkart with Amazon products as fallback
flipkart_products = flipkart_scraper.search_product(query, amazon_products)
print(f"Found {len(flipkart_products)} Flipkart products")

if flipkart_products:
    print("\nFirst Flipkart product details:")
    print(json.dumps(flipkart_products[0], indent=2))
    
    print("\nAll Flipkart product names:")
    for product in flipkart_products:
        print(f"- {product['name']} (₹{product['price']})")