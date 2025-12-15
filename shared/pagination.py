"""
Cursor-based pagination utilities
"""
from typing import Optional, List, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field
from sqlalchemy.orm import Query
from sqlalchemy import desc, asc
import base64
import json

T = TypeVar('T')


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters"""
    limit: int = Field(50, ge=1, le=100, description="Number of items per page")
    cursor: Optional[str] = Field(None, description="Cursor for pagination (base64 encoded)")
    direction: str = Field("next", pattern="^(next|prev)$", description="Pagination direction")
    
    def decode_cursor(self) -> Optional[Dict[str, Any]]:
        """Decode cursor to get pagination state"""
        if not self.cursor:
            return None
        try:
            decoded = base64.b64decode(self.cursor.encode()).decode()
            return json.loads(decoded)
        except Exception:
            return None
    
    @staticmethod
    def encode_cursor(data: Dict[str, Any]) -> str:
        """Encode pagination state as cursor"""
        encoded = json.dumps(data).encode()
        return base64.b64encode(encoded).decode()


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response with cursor"""
    items: List[T]
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    limit: int
    has_more: bool = False


def paginate_with_cursor(
    query: Query,
    limit: int,
    cursor: Optional[str] = None,
    sort_field: str = "created_at",
    sort_desc: bool = True,
    entity_class=None
) -> PaginatedResponse:
    """
    Apply cursor-based pagination to a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        limit: Number of items per page
        cursor: Cursor string (base64 encoded)
        sort_field: Field to sort by
        sort_desc: Sort in descending order
        entity_class: Entity class (optional, will try to infer from query)
    
    Returns:
        PaginatedResponse with items and cursors
    """
    # Get entity class
    if entity_class is None:
        # Try to get from query column_descriptions
        try:
            if query.column_descriptions:
                entity_class = query.column_descriptions[0]['entity']
            else:
                # Fallback: get from query class
                entity_class = query.column_descriptions[0].get('entity') if hasattr(query, 'column_descriptions') else None
        except (IndexError, AttributeError):
            # If we can't infer, try to get from query statement
            entity_class = None
    
    if entity_class is None:
        raise ValueError(f"Cannot determine entity class for sorting by {sort_field}")
    
    # Apply sorting
    sort_column = getattr(entity_class, sort_field, None)
    if sort_column is None:
        raise ValueError(f"Sort field {sort_field} not found on {entity_class.__name__}")
    
    if sort_desc:
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Decode cursor if provided
    cursor_data = None
    if cursor:
        try:
            decoded = base64.b64decode(cursor.encode()).decode()
            cursor_data = json.loads(decoded)
            
            # Apply cursor filter
            cursor_value = cursor_data.get('value')
            if cursor_value and sort_column:
                if sort_desc:
                    query = query.filter(sort_column < cursor_value)
                else:
                    query = query.filter(sort_column > cursor_value)
        except Exception:
            pass  # Invalid cursor, ignore
    
    # Get one extra item to check if there's more
    items = query.limit(limit + 1).all()
    has_more = len(items) > limit
    
    if has_more:
        items = items[:-1]  # Remove the extra item
    
    # Generate cursors
    next_cursor = None
    prev_cursor = None
    
    if items:
        # Next cursor (for next page)
        if has_more:
            last_item = items[-1]
            last_value = getattr(last_item, sort_field)
            next_cursor = CursorPaginationParams.encode_cursor({
                "value": last_value.isoformat() if hasattr(last_value, 'isoformat') else str(last_value),
                "field": sort_field
            })
        
        # Previous cursor (for previous page)
        if cursor_data:  # If we had a cursor, we can go back
            first_item = items[0]
            first_value = getattr(first_item, sort_field)
            prev_cursor = CursorPaginationParams.encode_cursor({
                "value": first_value.isoformat() if hasattr(first_value, 'isoformat') else str(first_value),
                "field": sort_field
            })
    
    return PaginatedResponse(
        items=items,
        next_cursor=next_cursor,
        prev_cursor=prev_cursor,
        limit=limit,
        has_more=has_more
    )


