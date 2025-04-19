import logging
from datetime import datetime
from typing import Dict, Optional, List, Any

from supabase import create_client, Client

from myapp.domain.repositories import UserRepository, DocumentRepository
from myapp.domain.models import User, Document

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('postgres_repository')


class SupabaseRepository:
    """Base repository for Supabase integration"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize the connection to Supabase"""
        try:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("Supabase connection established successfully")
        except Exception as e:
            logger.error(f"Error connecting to Supabase: {str(e)}")
            raise


class SupabaseUserRepository(SupabaseRepository, UserRepository):
    """User repository implementation using Supabase"""
    
    def create_user(self, email: str, name: str, password_hash: str) -> Dict[str, Any]:
        """Create a new user in the database"""
        try:
            # Create user data
            user_data = {
                "email": email,
                "name": name,
                "password_hash": password_hash,
                "is_verified": True  # User is immediately verified in this implementation
            }
            
            result = self.supabase.table("users").insert(user_data).execute()
            
            if result.data:
                logger.info(f"User {email} created successfully")
                return {
                    "success": True,
                    "user": result.data[0]
                }
            else:
                logger.error(f"Error creating user: {result.error}")
                return {"error": "Failed to create user"}
                
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return {"error": f"An error occurred: {str(e)}"}
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        try:
            result = self.supabase.table("users").select("*").eq("email", email).execute()
            
            if result.data and len(result.data) > 0:
                user_data = result.data[0]
                return User(
                    id=user_data["id"],
                    email=user_data["email"],
                    name=user_data["name"],
                    password_hash=user_data["password_hash"],
                    is_verified=user_data.get("is_verified", False),
                    avatar_url=user_data.get("avatar_url"),
                    verification_token=user_data.get("verification_token"),
                    verification_token_expires_at=user_data.get("verification_token_expires_at")
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        try:
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                user_data = result.data[0]
                return User(
                    id=user_data["id"],
                    email=user_data["email"],
                    name=user_data["name"],
                    password_hash=user_data["password_hash"],
                    is_verified=user_data.get("is_verified", False),
                    avatar_url=user_data.get("avatar_url"),
                    verification_token=user_data.get("verification_token"),
                    verification_token_expires_at=user_data.get("verification_token_expires_at")
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None
    
    def update_user_profile(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        try:
            # Ensure sensitive fields cannot be updated
            if "password_hash" in update_data:
                del update_data["password_hash"]
                
            result = self.supabase.table("users").update(update_data).eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"User {user_id} profile updated successfully")
                return {
                    "success": True,
                    "user": result.data[0]
                }
            else:
                logger.error(f"Error updating user profile: {result.error}")
                return {"error": "Failed to update user profile"}
                
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return {"error": f"An error occurred: {str(e)}"}


class SupabaseDocumentRepository(SupabaseRepository, DocumentRepository):
    """Document repository implementation using Supabase"""
    
    def save_document(self, user_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save document information in the database"""
        try:
            # Add user ID to document data
            document_data["user_id"] = user_id
            
            # Ensure document has a name
            if "document_name" not in document_data:
                document_data["document_name"] = "Untitled"
                
            # Add timestamps
            now = datetime.now().isoformat()
            document_data["created_at"] = now
            document_data["updated_at"] = now
            
            result = self.supabase.table("documents").insert(document_data).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Document saved successfully for user {user_id}")
                return {
                    "success": True,
                    "document": result.data[0]
                }
            else:
                logger.error(f"Error saving document: {result.error}")
                return {"error": "Failed to save document"}
                
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            return {"error": f"An error occurred: {str(e)}"}
    
    def get_user_documents(self, user_id: str) -> List[Document]:
        """Get all documents for a user"""
        try:
            result = self.supabase.table("documents").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            
            documents = []
            for doc_data in result.data:
                documents.append(Document(
                    id=doc_data["id"],
                    user_id=doc_data["user_id"],
                    document_name=doc_data["document_name"],
                    document_number=doc_data.get("document_number"),
                    operation_type=doc_data.get("operation_type"),
                    file_path=doc_data.get("file_path"),
                    file_size_kb=doc_data.get("file_size_kb"),
                    created_at=doc_data.get("created_at"),
                    updated_at=doc_data.get("updated_at"),
                    content=doc_data.get("content")
                ))
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting user documents: {str(e)}")
            return []
    
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """Get a document by ID"""
        try:
            result = self.supabase.table("documents").select("*").eq("id", document_id).execute()
            
            if result.data and len(result.data) > 0:
                doc_data = result.data[0]
                return Document(
                    id=doc_data["id"],
                    user_id=doc_data["user_id"],
                    document_name=doc_data["document_name"],
                    document_number=doc_data.get("document_number"),
                    operation_type=doc_data.get("operation_type"),
                    file_path=doc_data.get("file_path"),
                    file_size_kb=doc_data.get("file_size_kb"),
                    created_at=doc_data.get("created_at"),
                    updated_at=doc_data.get("updated_at"),
                    content=doc_data.get("content")
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting document by ID: {str(e)}")
            return None 