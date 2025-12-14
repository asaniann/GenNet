"""
Advanced search and filtering utilities
"""
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class FilterOperator(str, Enum):
    """Filter operators"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"
    REGEX = "regex"


class SortDirection(str, Enum):
    """Sort direction"""
    ASC = "asc"
    DESC = "desc"


class Filter:
    """Filter definition"""
    
    def __init__(self, field: str, operator: FilterOperator, value: Any):
        self.field = field
        self.operator = operator
        self.value = value
    
    def matches(self, item: Dict[str, Any]) -> bool:
        """Check if item matches filter"""
        field_value = item.get(self.field)
        
        if self.operator == FilterOperator.EQUALS:
            return field_value == self.value
        elif self.operator == FilterOperator.NOT_EQUALS:
            return field_value != self.value
        elif self.operator == FilterOperator.GREATER_THAN:
            return field_value is not None and field_value > self.value
        elif self.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return field_value is not None and field_value >= self.value
        elif self.operator == FilterOperator.LESS_THAN:
            return field_value is not None and field_value < self.value
        elif self.operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return field_value is not None and field_value <= self.value
        elif self.operator == FilterOperator.CONTAINS:
            if isinstance(field_value, str) and isinstance(self.value, str):
                return self.value.lower() in field_value.lower()
            return False
        elif self.operator == FilterOperator.STARTS_WITH:
            if isinstance(field_value, str) and isinstance(self.value, str):
                return field_value.lower().startswith(self.value.lower())
            return False
        elif self.operator == FilterOperator.ENDS_WITH:
            if isinstance(field_value, str) and isinstance(self.value, str):
                return field_value.lower().endswith(self.value.lower())
            return False
        elif self.operator == FilterOperator.IN:
            return field_value in self.value if isinstance(self.value, list) else False
        elif self.operator == FilterOperator.NOT_IN:
            return field_value not in self.value if isinstance(self.value, list) else True
        elif self.operator == FilterOperator.IS_NULL:
            return field_value is None
        elif self.operator == FilterOperator.IS_NOT_NULL:
            return field_value is not None
        elif self.operator == FilterOperator.BETWEEN:
            if isinstance(self.value, list) and len(self.value) == 2:
                return self.value[0] <= field_value <= self.value[1]
            return False
        elif self.operator == FilterOperator.REGEX:
            if isinstance(field_value, str):
                try:
                    return bool(re.search(self.value, field_value, re.IGNORECASE))
                except re.error:
                    return False
            return False
        
        return False


class SearchQuery:
    """Search query builder"""
    
    def __init__(self):
        self.filters: List[Filter] = []
        self.search_text: Optional[str] = None
        self.search_fields: List[str] = []
        self.sort_by: Optional[str] = None
        self.sort_direction: SortDirection = SortDirection.ASC
    
    def add_filter(self, field: str, operator: FilterOperator, value: Any) -> 'SearchQuery':
        """Add a filter"""
        self.filters.append(Filter(field, operator, value))
        return self
    
    def set_search(self, text: str, fields: List[str]) -> 'SearchQuery':
        """Set full-text search"""
        self.search_text = text
        self.search_fields = fields
        return self
    
    def set_sort(self, field: str, direction: SortDirection = SortDirection.ASC) -> 'SearchQuery':
        """Set sort order"""
        self.sort_by = field
        self.sort_direction = direction
        return self
    
    def matches(self, item: Dict[str, Any]) -> bool:
        """Check if item matches all filters and search"""
        # Check filters
        for filter_obj in self.filters:
            if not filter_obj.matches(item):
                return False
        
        # Check search text
        if self.search_text:
            if not self.search_fields:
                # Search all string fields
                search_lower = self.search_text.lower()
                for value in item.values():
                    if isinstance(value, str) and search_lower in value.lower():
                        return True
                return False
            else:
                # Search specific fields
                search_lower = self.search_text.lower()
                for field in self.search_fields:
                    field_value = item.get(field)
                    if isinstance(field_value, str) and search_lower in field_value.lower():
                        return True
                return False
        
        return True
    
    def apply(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply filters and search to items"""
        # Filter
        filtered = [item for item in items if self.matches(item)]
        
        # Sort
        if self.sort_by:
            reverse = self.sort_direction == SortDirection.DESC
            try:
                filtered.sort(key=lambda x: x.get(self.sort_by), reverse=reverse)
            except (TypeError, KeyError):
                logger.warning(f"Could not sort by field: {self.sort_by}")
        
        return filtered


def parse_query_params(params: Dict[str, Any]) -> SearchQuery:
    """
    Parse query parameters into SearchQuery
    
    Supports formats like:
    - filter[field]=value (equals)
    - filter[field][operator]=value (specific operator)
    - search=text
    - search_fields=field1,field2
    - sort=field
    - sort_direction=asc|desc
    """
    query = SearchQuery()
    
    # Parse filters
    for key, value in params.items():
        if key.startswith("filter["):
            # Extract field and operator
            match = re.match(r"filter\[([^\]]+)\](\[([^\]]+)\])?", key)
            if match:
                field = match.group(1)
                operator_str = match.group(3) if match.group(3) else "eq"
                
                try:
                    operator = FilterOperator(operator_str)
                    query.add_filter(field, operator, value)
                except ValueError:
                    logger.warning(f"Unknown filter operator: {operator_str}")
    
    # Parse search
    if "search" in params:
        search_text = params["search"]
        search_fields = params.get("search_fields", "").split(",")
        search_fields = [f.strip() for f in search_fields if f.strip()]
        query.set_search(search_text, search_fields)
    
    # Parse sort
    if "sort" in params:
        sort_field = params["sort"]
        sort_dir = SortDirection(params.get("sort_direction", "asc"))
        query.set_sort(sort_field, sort_dir)
    
    return query


def build_sqlalchemy_query(base_query, search_query: SearchQuery, model_class):
    """
    Build SQLAlchemy query from SearchQuery
    
    Usage:
        query = session.query(Network)
        query = build_sqlalchemy_query(query, search_query, Network)
        results = query.all()
    """
    # Apply filters
    for filter_obj in search_query.filters:
        field = getattr(model_class, filter_obj.field, None)
        if field is None:
            continue
        
        if filter_obj.operator == FilterOperator.EQUALS:
            base_query = base_query.filter(field == filter_obj.value)
        elif filter_obj.operator == FilterOperator.NOT_EQUALS:
            base_query = base_query.filter(field != filter_obj.value)
        elif filter_obj.operator == FilterOperator.GREATER_THAN:
            base_query = base_query.filter(field > filter_obj.value)
        elif filter_obj.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            base_query = base_query.filter(field >= filter_obj.value)
        elif filter_obj.operator == FilterOperator.LESS_THAN:
            base_query = base_query.filter(field < filter_obj.value)
        elif filter_obj.operator == FilterOperator.LESS_THAN_OR_EQUAL:
            base_query = base_query.filter(field <= filter_obj.value)
        elif filter_obj.operator == FilterOperator.CONTAINS:
            base_query = base_query.filter(field.contains(filter_obj.value))
        elif filter_obj.operator == FilterOperator.IN:
            base_query = base_query.filter(field.in_(filter_obj.value))
        elif filter_obj.operator == FilterOperator.NOT_IN:
            base_query = base_query.filter(~field.in_(filter_obj.value))
        elif filter_obj.operator == FilterOperator.IS_NULL:
            base_query = base_query.filter(field.is_(None))
        elif filter_obj.operator == FilterOperator.IS_NOT_NULL:
            base_query = base_query.filter(field.isnot(None))
        elif filter_obj.operator == FilterOperator.BETWEEN:
            if isinstance(filter_obj.value, list) and len(filter_obj.value) == 2:
                base_query = base_query.filter(field.between(filter_obj.value[0], filter_obj.value[1]))
    
    # Apply search (full-text search)
    if search_query.search_text and search_query.search_fields:
        from sqlalchemy import or_
        conditions = []
        for field_name in search_query.search_fields:
            field = getattr(model_class, field_name, None)
            if field is not None:
                conditions.append(field.contains(search_query.search_text))
        if conditions:
            base_query = base_query.filter(or_(*conditions))
    
    # Apply sort
    if search_query.sort_by:
        sort_field = getattr(model_class, search_query.sort_by, None)
        if sort_field is not None:
            if search_query.sort_direction == SortDirection.DESC:
                base_query = base_query.order_by(sort_field.desc())
            else:
                base_query = base_query.order_by(sort_field.asc())
    
    return base_query


