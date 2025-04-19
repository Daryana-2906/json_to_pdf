from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class User:
    """User domain model"""
    id: str
    name: str
    email: str
    password_hash: str
    is_verified: bool = False
    avatar_url: Optional[str] = None
    verification_token: Optional[str] = None
    verification_token_expires_at: Optional[datetime] = None


@dataclass
class Document:
    """Document domain model"""
    id: str
    user_id: str
    document_name: str
    document_number: Optional[str] = None
    operation_type: Optional[str] = None
    file_path: Optional[str] = None
    file_size_kb: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    content: Optional[Dict[str, Any]] = None 