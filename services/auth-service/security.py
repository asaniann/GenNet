"""
Security utilities for encryption and compliance
"""

import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


def get_encryption_key() -> bytes:
    """Get or generate encryption key"""
    key_str = os.getenv("ENCRYPTION_KEY")
    if key_str:
        return key_str.encode()
    # Generate key from password (in production, use AWS KMS)
    password = os.getenv("MASTER_PASSWORD", "default-password-change-in-production").encode()
    salt = os.getenv("ENCRYPTION_SALT", "default-salt").encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    f = Fernet(get_encryption_key())
    encrypted = f.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    f = Fernet(get_encryption_key())
    decoded = base64.urlsafe_b64decode(encrypted_data.encode())
    decrypted = f.decrypt(decoded)
    return decrypted.decode()

