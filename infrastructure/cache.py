"""
Cache implementation for the infrastructure layer
"""
from typing import Any, Optional
from caching import cache_manager, invalidate_transaction_cache

# Import and expose the cache functions from the caching module
get_from_cache = cache_manager.get
set_to_cache = cache_manager.set
delete_from_cache = cache_manager.delete

# Export the invalidate function
__all__ = [
    'get_from_cache',
    'set_to_cache',
    'delete_from_cache',
    'invalidate_transaction_cache'
]