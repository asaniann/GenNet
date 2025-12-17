"""
Database Query Optimization Utilities
Provides query optimization, connection pooling, and caching strategies
"""

import logging
from typing import Any, Dict, Optional, List
from functools import wraps
from sqlalchemy.orm import Session, Query
from sqlalchemy import text
from shared.cache import cached, get_cache_manager

logger = logging.getLogger(__name__)


def optimize_query(query: Query, limit: Optional[int] = None) -> Query:
    """
    Optimize SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        limit: Optional limit for results
        
    Returns:
        Optimized query
    """
    if limit:
        query = query.limit(limit)
    
    # Enable query result caching if available
    # query = query.execution_options(enable_cache=True)
    
    return query


def paginate_query(
    query: Query,
    page: int = 1,
    limit: int = 20,
    max_limit: int = 100
) -> Dict[str, Any]:
    """
    Paginate query results
    
    Args:
        query: SQLAlchemy query
        page: Page number (1-indexed)
        limit: Items per page
        max_limit: Maximum items per page
        
    Returns:
        Dictionary with paginated results and metadata
    """
    # Validate and normalize pagination
    if page < 1:
        page = 1
    if limit < 1:
        limit = 20
    if limit > max_limit:
        limit = max_limit
    
    # Get total count (optimized)
    total = query.count()
    
    # Calculate offset
    offset = (page - 1) * limit
    
    # Get paginated results
    items = query.offset(offset).limit(limit).all()
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1
    }


def cached_query(ttl: int = 3600):
    """
    Decorator to cache query results
    
    Usage:
        @cached_query(ttl=1800)
        def get_network(network_id: str, db: Session):
            return db.query(Network).filter_by(id=network_id).first()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract db session and query parameters
            db = None
            cache_key_parts = []
            
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                else:
                    cache_key_parts.append(str(arg))
            
            for key, value in kwargs.items():
                if key != 'db':
                    cache_key_parts.append(f"{key}:{value}")
            
            cache_key = f"query:{func.__name__}:{':'.join(cache_key_parts)}"
            
            # Try cache first
            cache_manager = get_cache_manager()
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for query: {cache_key}")
                return cached_result
            
            # Execute query
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def batch_load_relationships(query: Query, relationships: List[str]) -> Query:
    """
    Optimize query by batch loading relationships (eager loading)
    
    Args:
        query: SQLAlchemy query
        relationships: List of relationship names to eager load
        
    Returns:
        Query with eager loading configured
    """
    from sqlalchemy.orm import joinedload, selectinload
    
    for rel in relationships:
        # Use selectinload for better performance with many-to-many
        query = query.options(selectinload(rel))
    
    return query


def explain_query(query: Query, db: Session) -> Dict[str, Any]:
    """
    Explain query execution plan
    
    Args:
        query: SQLAlchemy query
        db: Database session
        
    Returns:
        Query execution plan
    """
    # Get SQL statement
    sql = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
    
    # Execute EXPLAIN
    explain_sql = f"EXPLAIN ANALYZE {sql}"
    result = db.execute(text(explain_sql))
    
    plan = {
        "sql": sql,
        "plan": [dict(row) for row in result]
    }
    
    return plan


def optimize_connection_pool(
    pool_size: int = 10,
    max_overflow: int = 20,
    pool_timeout: int = 30,
    pool_recycle: int = 3600
) -> Dict[str, Any]:
    """
    Get optimized connection pool configuration
    
    Args:
        pool_size: Number of connections to maintain
        max_overflow: Maximum overflow connections
        pool_timeout: Timeout for getting connection
        pool_recycle: Recycle connections after this many seconds
        
    Returns:
        Connection pool configuration dictionary
    """
    return {
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_timeout": pool_timeout,
        "pool_recycle": pool_recycle,
        "pool_pre_ping": True,  # Verify connections before using
        "echo": False  # Set to True for SQL logging in development
    }

