"""
Monitoring and logging module for the financial dashboard
"""
import logging
import sys
from datetime import datetime
import os
import psutil
import time
from functools import wraps
import traceback
from typing import Dict, Any

class MonitoringSetup:
    def __init__(self, log_level=logging.INFO, log_file='app.log'):
        self.log_level = log_level
        self.log_file = log_file
        self.setup_logging()
    
    def setup_logging(self):
        """Setup comprehensive logging with file and console handlers"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            f'logs/{self.log_file}',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        
        # Get root logger and add handlers
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear any existing handlers
        root_logger.handlers = []
        
        # Add handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics for monitoring"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
            'process_count': len(psutil.pids()),
            'uptime': time.time() - psutil.boot_time()
        }

# Global monitoring instance
monitoring = MonitoringSetup()

def log_performance(func):
    """Decorator to log function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger(func.__module__)
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(f"{func.__name__} executed in {execution_time:.4f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.4f}s: {str(e)}\n{traceback.format_exc()}")
            raise
    
    return wrapper

def log_user_activity(user_id: str, action: str, details: Dict[str, Any] = None):
    """Log user activity for audit trail"""
    logger = logging.getLogger('user_activity')
    log_data = {
        'user_id': user_id,
        'action': action,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    logger.info(f"User activity: {log_data}")

def log_business_metric(metric_name: str, value: Any, context: Dict[str, Any] = None):
    """Log important business metrics"""
    logger = logging.getLogger('business_metrics')
    log_data = {
        'metric': metric_name,
        'value': value,
        'timestamp': datetime.now().isoformat(),
        'context': context or {}
    }
    logger.info(f"Business metric: {log_data}")

# Initialize logger
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Example usage
    logger.info("Monitoring module initialized")
    
    # Test system metrics
    metrics = monitoring.get_system_metrics()
    print("System Metrics:", metrics)
    
    # Test decorated function
    @log_performance
    def sample_function():
        time.sleep(0.1)  # Simulate work
        return "Done"
    
    result = sample_function()
    print(f"Function result: {result}")