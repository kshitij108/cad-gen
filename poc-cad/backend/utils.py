"""
Security utilities and helper functions
"""
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os

# Configure bcrypt with explicit options to avoid version detection issues
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

def hash_password(password: str) -> str:
    """Hash a password for storage"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return os.path.splitext(filename)[1].lower()

def is_valid_file_type(filename: str, allowed_types: list) -> bool:
    """Check if file type is allowed"""
    return get_file_extension(filename) in allowed_types
