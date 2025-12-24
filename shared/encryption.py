"""
Encryption utilities for sensitive data
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class FieldEncryption:
    """Field-level encryption for sensitive data"""
    
    def __init__(self):
        """Initialize encryption"""
        # Get encryption key from environment
        encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if encryption_key:
            # Use provided key
            self.cipher = Fernet(encryption_key.encode())
        else:
            # Generate key from password (for development only)
            # In production, must use proper key management
            password = os.getenv("ENCRYPTION_PASSWORD", "dev-password-change-in-production").encode()
            salt = os.getenv("ENCRYPTION_SALT", "dev-salt").encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            self.cipher = Fernet(key)
    
    def encrypt(self, value: str) -> str:
        """
        Encrypt a string value
        
        Args:
            value: Value to encrypt
            
        Returns:
            Encrypted value (base64 encoded)
        """
        if not value:
            return value
        
        try:
            encrypted = self.cipher.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Error encrypting value: {e}")
            raise
    
    def decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt a string value
        
        Args:
            encrypted_value: Encrypted value (base64 encoded)
            
        Returns:
            Decrypted value
        """
        if not encrypted_value:
            return encrypted_value
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting value: {e}")
            raise


# Global instance
_field_encryption: Optional[FieldEncryption] = None


def get_field_encryption() -> FieldEncryption:
    """Get global field encryption instance"""
    global _field_encryption
    if _field_encryption is None:
        _field_encryption = FieldEncryption()
    return _field_encryption


def encrypt_field(value: str) -> str:
    """Encrypt a field value"""
    return get_field_encryption().encrypt(value)


def decrypt_field(encrypted_value: str) -> str:
    """Decrypt a field value"""
    return get_field_encryption().decrypt(encrypted_value)

