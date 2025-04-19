import logging
import time
from functools import wraps
from typing import Callable, Dict, Any, Optional


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create loggers
app_logger = logging.getLogger('app')
db_logger = logging.getLogger('database')
auth_logger = logging.getLogger('auth')
doc_logger = logging.getLogger('document')


class MetricsLogger:
    """Logger for application metrics"""
    
    def __init__(self, logger_name: str = 'metrics'):
        self.logger = logging.getLogger(logger_name)
        self.metrics: Dict[str, Dict[str, Any]] = {}
    
    def log_time(self, operation: str, elapsed_time: float):
        """Log operation time"""
        self.logger.info(f"Operation '{operation}' took {elapsed_time:.4f} seconds")
        
        if operation not in self.metrics:
            self.metrics[operation] = {
                'count': 0,
                'total_time': 0,
                'min_time': float('inf'),
                'max_time': 0
            }
            
        self.metrics[operation]['count'] += 1
        self.metrics[operation]['total_time'] += elapsed_time
        self.metrics[operation]['min_time'] = min(self.metrics[operation]['min_time'], elapsed_time)
        self.metrics[operation]['max_time'] = max(self.metrics[operation]['max_time'], elapsed_time)
    
    def log_error(self, operation: str, error: Exception):
        """Log error"""
        self.logger.error(f"Error in operation '{operation}': {str(error)}")
        
        if operation not in self.metrics:
            self.metrics[operation] = {'errors': 0}
        elif 'errors' not in self.metrics[operation]:
            self.metrics[operation]['errors'] = 0
            
        self.metrics[operation]['errors'] += 1
    
    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all recorded metrics"""
        return self.metrics
    
    def get_operation_metrics(self, operation: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific operation"""
        return self.metrics.get(operation)


# Create singleton instance
metrics_logger = MetricsLogger()


def timed(operation_name: str):
    """Decorator to time functions and log metrics"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                metrics_logger.log_time(operation_name, elapsed_time)
                return result
            except Exception as e:
                elapsed_time = time.time() - start_time
                metrics_logger.log_time(operation_name, elapsed_time)
                metrics_logger.log_error(operation_name, e)
                raise
        return wrapper
    return decorator 