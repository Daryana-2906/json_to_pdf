from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from myapp.domain.models import User, Document


class UserRepository(ABC):
    """User repository interface"""
    
    @abstractmethod
    def create_user(self, email: str, name: str, password_hash: str) -> Dict[str, Any]:
        """Create a new user"""
        pass
        
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        pass
        
    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        pass
        
    @abstractmethod
    def update_user_profile(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        pass


class DocumentRepository(ABC):
    """Document repository interface"""
    
    @abstractmethod
    def save_document(self, user_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save document information"""
        pass
        
    @abstractmethod
    def get_user_documents(self, user_id: str) -> List[Document]:
        """Get all documents for a user"""
        pass
        
    @abstractmethod
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """Get a document by ID"""
        pass 