# reset_db.py
from flask import Flask
from extensions import db
import pymysql
import os

# Use pymysql as MySQL driver
pymysql.install_as_MySQLdb()

# Create a Flask app for database operations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://wizard_user:wizard123@localhost/pricewizard'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)

def reset_database():
    with app.app_context():
        # Import models after initializing db
        from models.pricewizard_models import User, SearchHistory, PriceHistory, PriceAlert, Product, ProductReview
        
        # Drop all tables
        print("Dropping all tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating all tables...")
        db.create_all()
        
        # Create a test user
        print("Creating test user...")
        test_user = User(
            username="admin",
            email="admin@pricewizard.com"
        )
        test_user.set_password("admin123")
        
        db.session.add(test_user)
        db.session.commit()
        
        print(f"Test user created with ID: {test_user.id}")
        
        # Add some sample data
        print("Adding sample price history...")
        sample_products = [
            "iPhone 13 Pro Max",
            "Samsung Galaxy S21",
            "MacBook Pro 16-inch",
            "Sony PlayStation 5",
            "Nintendo Switch"
        ]
        
        platforms = ["amazon", "flipkart", "alibaba", "croma", "myntra", "ajio"]
        
        import random
        from datetime import datetime, timedelta
        
        # Add sample price history
        for product in sample_products:
            base_price = random.randint(10000, 80000)
            
            for platform in platforms:
                # Add 10 price points for each product/platform
                for i in range(10):
                    price_variation = random.uniform(0.9, 1.1)
                    price = base_price * price_variation
                    
                    timestamp = datetime.now() - timedelta(days=i)
                    
                    price_history = PriceHistory(
                        product_name=product,
                        platform=platform,
                        price=price,
                        url=f"https://www.{platform}.com/product/{product.lower().replace(' ', '-')}",
                        timestamp=timestamp
                    )
                    
                    db.session.add(price_history)
        
        # Add sample search history
        print("Adding sample search history...")
        search_terms = ["iPhone", "Samsung", "MacBook", "PlayStation", "Nintendo", "Laptop", "TV", "Headphones"]
        
        for term in search_terms:
            search = SearchHistory(
                query=term,
                user_id=test_user.id,
                timestamp=datetime.now() - timedelta(days=random.randint(0, 10))
            )
            
            db.session.add(search)
        
        # Add sample price alerts
        print("Adding sample price alerts...")
        for product in sample_products[:3]:
            alert = PriceAlert(
                user_id=test_user.id,
                product_name=product,
                target_price=random.randint(10000, 50000),
                platform=random.choice(platforms),
                status=random.choice(["Active", "Triggered", "Expired"])
            )
            
            db.session.add(alert)
        
        db.session.commit()
        print("Sample data added successfully!")
        
        print("Database reset complete!")

if __name__ == "__main__":
    reset_database()