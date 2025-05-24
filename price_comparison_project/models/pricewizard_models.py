# models/pricewizard_models.py
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pymysql

# Use pymysql as MySQL driver
pymysql.install_as_MySQLdb()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationships with explicit back references
    search_history = db.relationship(
        'SearchHistory',
        backref='user',
        lazy='dynamic',
        foreign_keys='SearchHistory.user_id'
    )
    
    price_alerts = db.relationship(
        'PriceAlert',
        backref='user',
        lazy='dynamic',
        foreign_keys='PriceAlert.user_id'
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @classmethod
    def create_user(cls, username, email, password):
        # Check if username or email already exists
        existing_user = db.session.query(cls).filter((cls.username == username) | (cls.email == email)).first()
        
        if existing_user:
            return None
            
        # Create new user
        user = cls(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @classmethod
    def authenticate(cls, username, password):
        user = db.session.query(cls).filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        return None
    
    def __repr__(self):
        return f'<User {self.username}>'


class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Changed from 'user.id' to 'users.id'
    query = db.Column(db.String(255))  # Keep only the query field that exists in your database
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SearchHistory {self.query}>'


class PriceHistory(db.Model):
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    url = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PriceHistory {self.product_name} - {self.platform} - {self.price}>'


class PriceAlert(db.Model):
    __tablename__ = 'price_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    target_price = db.Column(db.Float, nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PriceAlert {self.product_name} - {self.target_price}>'


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviews = db.relationship(
        'ProductReview', 
        backref='product', 
        lazy='dynamic',
        foreign_keys='ProductReview.product_id'
    )
    
    def __repr__(self):
        return f'<Product {self.name}>'


class ProductReview(db.Model):
    __tablename__ = 'product_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    content = db.Column(db.Text, nullable=True)
    sentiment = db.Column(db.String(20), nullable=True)  # positive, neutral, negative
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductReview {self.product_id} - {self.platform} - {self.rating}>'