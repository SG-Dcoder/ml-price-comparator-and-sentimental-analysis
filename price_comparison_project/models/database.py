# models/database.py
from extensions import db
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Use pymysql as MySQL driver
pymysql.install_as_MySQLdb()

# Database connection string
DATABASE_URI = 'mysql+pymysql://wizard_user:wizard123@localhost/pricewizard'

def get_db_engine():
    """Get a SQLAlchemy engine for direct SQL queries"""
    return create_engine(DATABASE_URI)

def get_db_session():
    """Get a SQLAlchemy session for ORM operations"""
    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def execute_query(query, params=None):
    """Execute a raw SQL query and return results"""
    engine = get_db_engine()
    with engine.connect() as connection:
        if params:
            result = connection.execute(text(query), params)
        else:
            result = connection.execute(text(query))
        return result.fetchall()

def execute_update(query, params=None):
    """Execute an update/insert/delete SQL query"""
    engine = get_db_engine()
    with engine.connect() as connection:
        if params:
            result = connection.execute(text(query), params)
        else:
            result = connection.execute(text(query))
        connection.commit()
        return result.rowcount

def init_db():
    """Initialize database tables if they don't exist"""
    from models.pricewizard_models import User, SearchHistory, PriceHistory, PriceAlert, Product, ProductReview
    
    # Create all tables
    db.create_all()
    
    # Check if admin user exists, create if not
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@pricewizard.com')
        admin.password = 'admin123'  # This will be hashed
        db.session.add(admin)
        db.session.commit()
        print("Admin user created")
    
    print("Database initialized successfully")

def reset_db():
    """Reset the database (drop and recreate all tables)"""
    from models.pricewizard_models import User, SearchHistory, PriceHistory, PriceAlert, Product, ProductReview
    
    # Drop all tables
    db.drop_all()
    
    # Recreate all tables
    db.create_all()
    
    print("Database reset successfully")