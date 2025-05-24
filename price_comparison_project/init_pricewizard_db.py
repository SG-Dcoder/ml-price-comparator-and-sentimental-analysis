# init_pricewizard_db.py
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

# Import models after initializing db
from models.pricewizard_models import User, SearchHistory, PriceAlert, Product, ProductReview, PriceHistory

def init_database():
    with app.app_context():
        # Create all tables
        print("Creating all tables...")
        db.create_all()
        
        # Create a test user
        print("Creating test user...")
        test_user = User.query.filter_by(username='admin').first()
        
        if not test_user:
            test_user = User(
                username="admin",
                email="admin@pricewizard.com"
            )
            test_user.password = "admin123"
            
            db.session.add(test_user)
            db.session.commit()
            
            print(f"Test user created with ID: {test_user.id}")
        else:
            print("Admin user already exists")
        
        print("Database initialization complete!")

if __name__ == "__main__":
    init_database()