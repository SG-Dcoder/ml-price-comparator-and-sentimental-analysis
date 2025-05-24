import os
import json
import time
import hashlib
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def cached(expiry=3600):
    """
    Decorator to cache function results to a file.
    
    Args:
        expiry: Cache expiry time in seconds (default: 1 hour)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache directory if it doesn't exist
            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'cache')
            os.makedirs(cache_dir, exist_ok=True)
            
            # Create a cache key based on function name and arguments
            key_parts = [func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            
            # Create a hash of the key parts
            cache_key = hashlib.md5(''.join(key_parts).encode()).hexdigest()
            cache_file = os.path.join(cache_dir, f"{cache_key}.json")
            
            # Check if cache file exists and is not expired
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    # Check if cache is still valid
                    if time.time() - cache_data['timestamp'] < expiry:
                        logger.info(f"Cache hit for {func.__name__}")
                        return cache_data['result']
                    else:
                        logger.info(f"Cache expired for {func.__name__}")
                except Exception as e:
                    logger.error(f"Error reading cache: {str(e)}")
            
            # Call the function and cache the result
            result = func(*args, **kwargs)
            
            try:
                with open(cache_file, 'w') as f:
                    json.dump({
                        'timestamp': time.time(),
                        'result': result
                    }, f)
                logger.info(f"Cached result for {func.__name__}")
            except Exception as e:
                logger.error(f"Error writing cache: {str(e)}")
            
            return result
        return wrapper
    return decorator