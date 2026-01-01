"""
Caching module for performance optimization
"""
import hashlib
import json
import time
from functools import wraps
from datetime import datetime, timedelta
import logging
import sqlite3
from database import get_db_connection

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, default_ttl=300):  # 5 minutes default TTL
        self.default_ttl = default_ttl
        self.init_cache_table()
    
    def init_cache_table(self):
        """Initialize cache table in database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for faster expiration checks
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)')
            
            conn.commit()
            conn.close()
            
            logger.info("Cache table initialized")
            
        except Exception as e:
            logger.error(f"Error initializing cache table: {str(e)}")
            raise e
    
    def _generate_key(self, func_name, args, kwargs):
        """Generate cache key from function name and parameters"""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, key):
        """Get value from cache"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT value FROM cache 
                WHERE key = ? AND expires_at > CURRENT_TIMESTAMP
            ''', (key,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None
    
    def set(self, key, value, ttl=None):
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache (key, value, expires_at)
                VALUES (?, ?, ?)
            ''', (key, json.dumps(value, default=str), expires_at))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
    
    def delete(self, key):
        """Delete value from cache"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
    
    def clear_expired(self):
        """Clear expired cache entries"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM cache WHERE expires_at <= CURRENT_TIMESTAMP')
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"Cleared {deleted_count} expired cache entries")
                
        except Exception as e:
            logger.error(f"Error clearing expired cache: {str(e)}")
    
    def cache_function(self, ttl=None):
        """Decorator to cache function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                key = self._generate_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                cached_result = self.get(key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for function: {func.__name__}")
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(key, result, ttl)
                
                logger.debug(f"Cached result for function: {func.__name__}")
                return result
            return wrapper
        return decorator

# Initialize global cache manager
cache_manager = CacheManager()

# Common caching functions for the financial dashboard
def cache_exchange_rates(ttl=3600):  # 1 hour TTL for exchange rates
    """Cache exchange rates with 1 hour TTL"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"exchange_rates_{args}_{str(kwargs)}"
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache_manager.set(key, result, ttl)
            return result
        return wrapper
    return decorator

def cache_report_data(ttl=1800):  # 30 minutes TTL for reports
    """Cache report data with 30 minute TTL"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"report_{func.__name__}_{args}_{str(kwargs)}"
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache_manager.set(key, result, ttl)
            return result
        return wrapper
    return decorator

def cache_financial_summary(ttl=900):  # 15 minutes TTL for financial summary
    """Cache financial summary with 15 minute TTL"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"financial_summary_{args}_{str(kwargs)}"
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache_manager.set(key, result, ttl)
            return result
        return wrapper
    return decorator

# Background job processing functions
def background_job_processor():
    """Process background jobs like OCR and bank syncs"""
    import threading
    import queue
    import time
    
    job_queue = queue.Queue()
    
    def worker():
        while True:
            try:
                job = job_queue.get(timeout=1)
                if job is None:
                    break
                
                job_type, job_data = job
                logger.info(f"Processing background job: {job_type}")
                
                if job_type == "ocr_processing":
                    # Process OCR job
                    process_ocr_job(job_data)
                elif job_type == "bank_sync":
                    # Process bank sync job
                    process_bank_sync_job(job_data)
                elif job_type == "report_generation":
                    # Process report generation job
                    process_report_job(job_data)
                
                job_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing background job: {str(e)}")
    
    # Start worker thread
    worker_thread = threading.Thread(target=worker, daemon=True)
    worker_thread.start()
    
    return job_queue

def process_ocr_job(job_data):
    """Process OCR job in background"""
    try:
        from ai_automation import AIProcessor
        processor = AIProcessor()
        
        # Extract text from receipt
        text = processor.extract_text_from_receipt(job_data['image_path'])
        
        # Extract financial data
        financial_data = processor.extract_financial_data(text)
        
        logger.info(f"OCR processing completed for {job_data['image_path']}")
        
        # Update status or save results as needed
        # This would typically update a database record or trigger a callback
        
    except Exception as e:
        logger.error(f"Error in OCR processing: {str(e)}")

def process_bank_sync_job(job_data):
    """Process bank sync job in background"""
    try:
        from bank_integration import BankIntegration
        bank_integration = BankIntegration()
        
        # Import bank transactions
        bank_integration.import_bank_transactions(
            job_data['bank_account_id'],
            job_data['transactions_data']
        )
        
        logger.info(f"Bank sync completed for account {job_data['bank_account_id']}")
        
    except Exception as e:
        logger.error(f"Error in bank sync: {str(e)}")

def process_report_job(job_data):
    """Process report generation job in background"""
    try:
        from advanced_reporting import AdvancedReporting
        reporter = AdvancedReporting()
        
        # Generate the requested report
        if job_data['report_type'] == 'cash_flow':
            report = reporter.cash_flow_forecasting(job_data.get('months_ahead', 6))
        elif job_data['report_type'] == 'variance':
            report = reporter.budget_variance_analysis(job_data.get('variance_threshold', 0.1))
        elif job_data['report_type'] == 'ratios':
            report = reporter.financial_ratios_analysis()
        else:
            logger.warning(f"Unknown report type: {job_data['report_type']}")
            return
        
        logger.info(f"Report generation completed: {job_data['report_type']}")
        
        # Save or process the report as needed
        
    except Exception as e:
        logger.error(f"Error in report generation: {str(e)}")

# Initialize background job processor
background_jobs = background_job_processor()