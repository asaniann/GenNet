"""
API Key Management for programmatic access
"""
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Try to import database models
try:
    from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
    from sqlalchemy.ext.declarative import declarative_base
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Base = None


class APIKeyScope(str, Enum):
    """API Key permission scopes"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    READ_NETWORKS = "read:networks"
    WRITE_NETWORKS = "write:networks"
    READ_WORKFLOWS = "read:workflows"
    WRITE_WORKFLOWS = "write:workflows"
    EXECUTE_WORKFLOWS = "execute:workflows"


class APIKey:
    """API Key model (if SQLAlchemy available)"""
    if SQLALCHEMY_AVAILABLE:
        __tablename__ = "api_keys"
        
        id = Column(Integer, primary_key=True, index=True)
        key_hash = Column(String, unique=True, nullable=False, index=True)
        key_prefix = Column(String, nullable=False)  # First 8 chars for identification
        name = Column(String, nullable=False)
        description = Column(Text)
        user_id = Column(Integer, nullable=False, index=True)
        scopes = Column(Text)  # Comma-separated list of scopes
        is_active = Column(Boolean, default=True)
        last_used_at = Column(DateTime)
        expires_at = Column(DateTime)
        created_at = Column(DateTime, default=datetime.utcnow)
        created_by = Column(Integer)


class APIKeyManager:
    """
    Manages API keys for programmatic access
    
    Features:
    - Secure key generation
    - Scoped permissions
    - Expiration support
    - Usage tracking
    - Revocation
    """
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self._key_cache: Dict[str, Dict[str, Any]] = {}
    
    def generate_key(
        self,
        user_id: int,
        name: str,
        scopes: List[APIKeyScope],
        expires_in_days: Optional[int] = None,
        description: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a new API key
        
        Returns:
            Dict with 'key' (the plaintext key) and 'key_id'
            The key should be shown to user once and stored securely
        """
        # Generate random key (64 bytes = 512 bits)
        raw_key = secrets.token_urlsafe(64)
        
        # Create prefix for identification (first 8 chars)
        key_prefix = raw_key[:8]
        
        # Hash the key for storage (SHA-256)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Store in database if available
        if self.db_session and SQLALCHEMY_AVAILABLE:
            api_key = APIKey(
                key_hash=key_hash,
                key_prefix=key_prefix,
                name=name,
                description=description,
                user_id=user_id,
                scopes=",".join(scope.value for scope in scopes),
                expires_at=expires_at,
                created_by=created_by or user_id,
                created_at=datetime.utcnow()
            )
            self.db_session.add(api_key)
            self.db_session.commit()
            key_id = api_key.id
        else:
            # In-memory storage for testing
            key_id = len(self._key_cache)
            self._key_cache[raw_key] = {
                "key_hash": key_hash,
                "key_prefix": key_prefix,
                "name": name,
                "user_id": user_id,
                "scopes": [scope.value for scope in scopes],
                "expires_at": expires_at,
                "created_at": datetime.utcnow()
            }
        
        logger.info(f"API key generated for user {user_id}: {key_prefix}...")
        
        return {
            "key": f"gennet_{key_prefix}_{raw_key[8:]}",  # Prefixed format
            "key_id": key_id,
            "key_prefix": key_prefix,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "scopes": [scope.value for scope in scopes]
        }
    
    def validate_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key
        
        Args:
            api_key: The API key string (format: gennet_<prefix>_<rest>)
        
        Returns:
            Dict with user_id and scopes if valid, None otherwise
        """
        # Parse key format: gennet_<prefix>_<rest>
        if not api_key.startswith("gennet_"):
            return None
        
        parts = api_key[7:].split("_", 1)  # Remove "gennet_" prefix
        if len(parts) != 2:
            return None
        
        prefix, rest = parts
        raw_key = prefix + rest
        
        # Hash and look up
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Check database
        if self.db_session and SQLALCHEMY_AVAILABLE:
            api_key_record = self.db_session.query(APIKey).filter(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            ).first()
            
            if not api_key_record:
                return None
            
            # Check expiration
            if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
                return None
            
            # Update last used
            api_key_record.last_used_at = datetime.utcnow()
            self.db_session.commit()
            
            return {
                "user_id": api_key_record.user_id,
                "scopes": api_key_record.scopes.split(",") if api_key_record.scopes else [],
                "key_id": api_key_record.id,
                "name": api_key_record.name
            }
        else:
            # Check cache
            if raw_key in self._key_cache:
                key_data = self._key_cache[raw_key]
                if key_data["key_hash"] == key_hash:
                    # Check expiration
                    if key_data.get("expires_at") and key_data["expires_at"] < datetime.utcnow():
                        return None
                    
                    return {
                        "user_id": key_data["user_id"],
                        "scopes": key_data["scopes"],
                        "key_id": hash(raw_key),
                        "name": key_data["name"]
                    }
        
        return None
    
    def revoke_key(self, key_id: int) -> bool:
        """Revoke an API key"""
        if self.db_session and SQLALCHEMY_AVAILABLE:
            api_key = self.db_session.query(APIKey).filter(APIKey.id == key_id).first()
            if api_key:
                api_key.is_active = False
                self.db_session.commit()
                logger.info(f"API key {key_id} revoked")
                return True
        return False
    
    def list_keys(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List API keys (without exposing full keys)"""
        if self.db_session and SQLALCHEMY_AVAILABLE:
            query = self.db_session.query(APIKey)
            if user_id:
                query = query.filter(APIKey.user_id == user_id)
            
            keys = query.all()
            return [
                {
                    "id": key.id,
                    "name": key.name,
                    "description": key.description,
                    "key_prefix": key.key_prefix,
                    "scopes": key.scopes.split(",") if key.scopes else [],
                    "is_active": key.is_active,
                    "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                    "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                    "created_at": key.created_at.isoformat()
                }
                for key in keys
            ]
        return []


def has_scope(required_scope: APIKeyScope, user_scopes: List[str]) -> bool:
    """Check if user has required scope"""
    # Admin scope has all permissions
    if APIKeyScope.ADMIN.value in user_scopes:
        return True
    
    # Exact match
    if required_scope.value in user_scopes:
        return True
    
    # Check hierarchical scopes
    scope_hierarchy = {
        APIKeyScope.READ.value: [APIKeyScope.READ_NETWORKS.value, APIKeyScope.READ_WORKFLOWS.value],
        APIKeyScope.WRITE.value: [APIKeyScope.WRITE_NETWORKS.value, APIKeyScope.WRITE_WORKFLOWS.value],
    }
    
    for parent, children in scope_hierarchy.items():
        if parent in user_scopes and required_scope.value in children:
            return True
    
    return False


# Global instance
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager(db_session=None) -> APIKeyManager:
    """Get or create global API key manager"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager(db_session=db_session)
    return _api_key_manager


