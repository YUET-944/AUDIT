"""
Caching module for performance optimization with Redis support
"""
import hashlib
import json
import time
import os
from functools import wraps
from datetime import datetime, timedelta
import logging
import redis
from database import get_db_connection

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, default_ttl=300):  # 5 minutes default TTL
        self.default_ttl = default_ttl
        
        # Connect to Redis
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        
        try:
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            # Fallback to in-memory cache if Redis is not available
            self.redis_client = None
            
        self.init_cache_table()
    
    def init_cache_table(self):
        """Initialize cache - for Redis this is just a placeholder"""
        if self.redis_client:
            logger.info("Using Redis for caching")
        else:
            logger.warning("Redis unavailable, using fallback")
            # Fallback to SQLite cache if Redis is not available
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
                
                logger.info("SQLite cache table initialized as fallback")
                
            except Exception as e:
                logger.error(f"Error initializing SQLite cache table: {str(e)}")
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
            if self.redis_client:
                # Try to get from Redis
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
                return None
            else:
                # Fallback to SQLite cache
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
            
            if self.redis_client:
                # Set in Redis with TTL
                self.redis_client.setex(key, ttl, json.dumps(value, default=str))
            else:
                # Fallback to SQLite cache
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
            if self.redis_client:
                # Delete from Redis
                self.redis_client.delete(key)
            else:
                # Fallback to SQLite cache
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
                
                conn.commit()
                conn.close()
            
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
    
    def clear_expired(self):
        """Clear expired cache entries - Redis handles expiration automatically"""
        try:
            if not self.redis_client:
                # Only needed for SQLite fallback
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
def cache_exchange_rates(ttl=1800):  # 30 minutes TTL for exchange rates
    """Cache exchange rates with 30 minute TTL"""
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

def cache_report_data(ttl=900):  # 15 minutes TTL for reports
    """Cache report data with 15 minute TTL"""
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

def cache_financial_summary(ttl=300):  # 5 minutes TTL for financial summary
    """Cache financial summary with 5 minute TTL"""
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

def cache_dashboard_kpis(ttl=300):  # 5 minutes TTL for dashboard KPIs
    """Cache dashboard KPIs with 5 minute TTL"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"dashboard_kpis_{args}_{str(kwargs)}"
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache_manager.set(key, result, ttl)
            return result
        return wrapper
    return decorator

def cache_user_permissions(ttl=1800):  # 30 minutes TTL for user permissions
    """Cache user permissions with 30 minute TTL"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"user_permissions_{args[0]}" if args else f"user_permissions_{kwargs.get('user_id')}"
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache_manager.set(key, result, ttl)
            return result
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern):
    """Invalidate cache entries matching a pattern"""
    # This would be implemented based on the specific cache backend
    # For Redis, you could use KEYS command with pattern matching
    # For SQLite cache, you'd need to implement a similar mechanism
    pass

def invalidate_transaction_cache():
    """Invalidate all transaction-related cache when transactions are updated"""
    # Invalidate all report caches when transactions change
    invalidate_cache_pattern("report_*")
    invalidate_cache_pattern("financial_summary_*")
    invalidate_cache_pattern("dashboard_kpis_*")

def background_job_processor():
    """Return the global background job processor instance"""
    return background_jobs

# Background job processing functions
class BackgroundJobProcessor:
    def __init__(self):
        import queue
        self.job_queue = queue.Queue()
        self.is_running = True
        self.start_workers()
    
    def start_workers(self, num_workers=3):
        """Start multiple worker threads for processing jobs"""
        import threading
        
        for i in range(num_workers):
            worker_thread = threading.Thread(target=self.worker, daemon=True, name=f"BackgroundWorker-{i}")
            worker_thread.start()
    
    def worker(self):
        """Worker function to process jobs from the queue"""
        import time
        import queue
        
        while self.is_running:
            try:
                job = self.job_queue.get(timeout=1)
                if job is None:
                    break
                
                job_type, job_data, job_id = job
                logger.info(f"Processing background job {job_id}: {job_type}")
                
                # Process the job based on type
                result = None
                success = False
                
                try:
                    if job_type == "ocr_processing":
                        result = self.process_ocr_job(job_data)
                        success = True
                    elif job_type == "bank_sync":
                        result = self.process_bank_sync_job(job_data)
                        success = True
                    elif job_type == "report_generation":
                        result = self.process_report_job(job_data)
                        success = True
                    elif job_type == "data_export":
                        result = self.process_data_export_job(job_data)
                        success = True
                    elif job_type == "backup":
                        result = self.process_backup_job(job_data)
                        success = True
                    else:
                        logger.error(f"Unknown job type: {job_type}")
                        success = False
                        
                except Exception as e:
                    logger.error(f"Error processing job {job_id} ({job_type}): {str(e)}")
                    success = False
                    
                # Update job status or perform callbacks
                if success:
                    logger.info(f"Job {job_id} completed successfully")
                else:
                    logger.error(f"Job {job_id} failed")
                    
                self.job_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Unexpected error in worker: {str(e)}")
    
    def process_ocr_job(self, job_data):
        """Process OCR job"""
        from ai_automation import AIProcessor
        processor = AIProcessor()
        
        # Extract text from receipt
        text = processor.extract_text_from_receipt(job_data['image_path'])
        
        # Extract financial data
        financial_data = processor.extract_financial_data(text)
        
        logger.info(f"OCR processing completed for {job_data['image_path']}")
        return financial_data
    
    def process_bank_sync_job(self, job_data):
        """Process bank sync job"""
        from bank_integration import BankIntegration
        bank_integration = BankIntegration()
        
        # Import bank transactions
        bank_integration.import_bank_transactions(
            job_data['bank_account_id'],
            job_data['transactions_data']
        )
        
        logger.info(f"Bank sync completed for account {job_data['bank_account_id']}")
        return True
    
    def process_report_job(self, job_data):
        """Process report generation job"""
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
            return None
        
        logger.info(f"Report generation completed: {job_data['report_type']}")
        return report
    
    def process_data_export_job(self, job_data):
        """Process data export job"""
        import pandas as pd
        from database import get_transactions, get_employees, get_budgets, get_investments, get_loans
        
        # Export data based on type
        if job_data['export_type'] == 'transactions':
            data = get_transactions()
            filename = f"transactions_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        elif job_data['export_type'] == 'employees':
            data = get_employees()
            filename = f"employees_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        elif job_data['export_type'] == 'budgets':
            data = get_budgets()
            filename = f"budgets_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            logger.warning(f"Unknown export type: {job_data['export_type']}")
            return None
        
        # Save to file
        data.to_csv(filename, index=False)
        logger.info(f"Data export completed: {filename}")
        return filename
    
    def process_backup_job(self, job_data):
        """Process backup job"""
        from backup_restore import backup_manager
        
        backup_path = backup_manager.create_compressed_backup(
            f"scheduled_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        )
        logger.info(f"Backup completed: {backup_path}")
        return backup_path
    
    def add_job(self, job_type, job_data):
        """Add a job to the queue"""
        import uuid
        job_id = str(uuid.uuid4())
        self.job_queue.put((job_type, job_data, job_id))
        logger.info(f"Added job {job_id} of type {job_type} to queue")
        return job_id
    
    def get_queue_size(self):
        """Get the current size of the job queue"""
        return self.job_queue.qsize()

# Initialize background job processor
background_jobs = BackgroundJobProcessor()

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