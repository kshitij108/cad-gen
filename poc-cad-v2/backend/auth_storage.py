"""
User authentication storage using JSON files
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid
from jose import jwt, JWTError
from utils import hash_password, verify_password

USERS_DIR = Path("./users")
USERS_DIR.mkdir(exist_ok=True)

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


class AuthManager:
    @staticmethod
    def register_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user"""
        email = user_data.get("email")
        
        # Check if user already exists
        existing_user = AuthManager.get_user_by_email(email)
        if existing_user:
            return {
                "status": "error",
                "message": "User with this email already exists"
            }
        
        user_id = str(uuid.uuid4())
        user = {
            "user_id": user_id,
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "email": email,
            "phone": user_data.get("phone"),
            "password_hash": hash_password(user_data.get("password")),
            "company_name": user_data.get("company_name"),
            "nature_of_business": user_data.get("nature_of_business"),
            "website": user_data.get("website"),
            "address": user_data.get("address"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        AuthManager._save_user(user)
        
        return {
            "status": "success",
            "message": "User registered successfully",
            "user_id": user_id,
            "email": email
        }
    
    @staticmethod
    def login(email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return token"""
        user = AuthManager.get_user_by_email(email)
        
        if not user:
            return {
                "status": "error",
                "message": "Invalid email or password"
            }
        
        if not verify_password(password, user.get("password_hash")):
            return {
                "status": "error",
                "message": "Invalid email or password"
            }
        
        # Generate token
        token_data = {
            "user_id": user.get("user_id"),
            "email": email,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "status": "success",
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.get("user_id"),
            "email": email,
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name")
        }
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        user_file = USERS_DIR / f"{email.replace('@', '_at_').replace('.', '_')}.json"
        if user_file.exists():
            with open(user_file) as f:
                return json.load(f)
        return None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user ID"""
        for user_file in USERS_DIR.glob("*.json"):
            with open(user_file) as f:
                user = json.load(f)
                if user.get("user_id") == user_id:
                    return user
        return None
    
    @staticmethod
    def _save_user(user: Dict[str, Any]) -> None:
        """Save user to file"""
        email = user.get("email")
        user_file = USERS_DIR / f"{email.replace('@', '_at_').replace('.', '_')}.json"
        with open(user_file, 'w') as f:
            json.dump(user, f, indent=2)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
