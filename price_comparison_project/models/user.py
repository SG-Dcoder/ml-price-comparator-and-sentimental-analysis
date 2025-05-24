# models/user.py
from models.pricewizard_models import User
from extensions import db
from flask_login import current_user
from werkzeug.security import generate_password_hash

def get_user_by_id(user_id):
    """Get a user by ID"""
    return User.query.get(user_id)

def get_user_by_username(username):
    """Get a user by username"""
    return User.query.filter_by(username=username).first()

def create_user(username, email, password):
    """Create a new user"""
    return User.create_user(username, email, password)

def update_user_profile(user_id, data):
    """Update user profile information"""
    user = User.query.get(user_id)
    if not user:
        return False
    
    # Update fields if provided
    if 'email' in data:
        user.email = data['email']
    
    if 'password' in data and data['password']:
        user.password = data['password']
    
    db.session.commit()
    return True

def get_user_search_history(user_id, limit=10):
    """Get user's search history"""
    user = User.query.get(user_id)
    if not user:
        return []
    
    return user.search_history.order_by(db.desc('timestamp')).limit(limit).all()

def get_user_price_alerts(user_id):
    """Get user's price alerts"""
    user = User.query.get(user_id)
    if not user:
        return []
    
    return user.price_alerts.all()

def add_price_alert(user_id, product_name, target_price, platform):
    """Add a new price alert for a user"""
    from models.pricewizard_models import PriceAlert
    
    alert = PriceAlert(
        user_id=user_id,
        product_name=product_name,
        target_price=target_price,
        platform=platform,
        status='Active'
    )
    
    db.session.add(alert)
    db.session.commit()
    return alert

def delete_price_alert(alert_id, user_id):
    """Delete a price alert if it belongs to the user"""
    from models.pricewizard_models import PriceAlert
    
    alert = PriceAlert.query.get(alert_id)
    if alert and alert.user_id == user_id:
        db.session.delete(alert)
        db.session.commit()
        return True
    return False

def is_authenticated():
    """Check if current user is authenticated"""
    return current_user.is_authenticated