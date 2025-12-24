"""
Advanced search and filtering utilities
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Query
from sqlalchemy import or_, and_
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AdvancedSearch:
    """Advanced search and filtering"""
    
    @staticmethod
    def apply_filters(
        query: Query,
        model_class: Any,
        filters: Dict[str, Any]
    ) -> Query:
        """
        Apply advanced filters to query
        
        Args:
            query: SQLAlchemy query
            model_class: Model class
            filters: Dictionary of filters
            
        Returns:
            Filtered query
        """
        for field, value in filters.items():
            if not hasattr(model_class, field):
                continue
            
            if isinstance(value, dict):
                # Complex filter (range, contains, etc.)
                if "gte" in value:
                    query = query.filter(getattr(model_class, field) >= value["gte"])
                if "lte" in value:
                    query = query.filter(getattr(model_class, field) <= value["lte"])
                if "gt" in value:
                    query = query.filter(getattr(model_class, field) > value["gt"])
                if "lt" in value:
                    query = query.filter(getattr(model_class, field) < value["lt"])
                if "contains" in value:
                    query = query.filter(getattr(model_class, field).contains(value["contains"]))
                if "in" in value:
                    query = query.filter(getattr(model_class, field).in_(value["in"]))
            else:
                # Simple equality filter
                query = query.filter(getattr(model_class, field) == value)
        
        return query
    
    @staticmethod
    def apply_search(
        query: Query,
        model_class: Any,
        search_term: str,
        search_fields: List[str]
    ) -> Query:
        """
        Apply full-text search
        
        Args:
            query: SQLAlchemy query
            model_class: Model class
            search_term: Search term
            search_fields: List of fields to search
            
        Returns:
            Query with search applied
        """
        if not search_term:
            return query
        
        conditions = []
        for field in search_fields:
            if hasattr(model_class, field):
                conditions.append(getattr(model_class, field).ilike(f"%{search_term}%"))
        
        if conditions:
            query = query.filter(or_(*conditions))
        
        return query
    
    @staticmethod
    def apply_sorting(
        query: Query,
        model_class: Any,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> Query:
        """
        Apply sorting to query
        
        Args:
            query: SQLAlchemy query
            model_class: Model class
            sort_by: Field to sort by
            sort_order: Sort order ("asc" or "desc")
            
        Returns:
            Sorted query
        """
        if not sort_by or not hasattr(model_class, sort_by):
            return query
        
        field = getattr(model_class, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(field.desc())
        else:
            query = query.order_by(field.asc())
        
        return query
