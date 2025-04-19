import unittest
from unittest.mock import MagicMock, patch
from myapp.internal.adapters.postgres.supabase_repository import SupabaseRepository
from myapp.internal.domain.models import User, Document
from datetime import datetime


class TestSupabaseRepository(unittest.TestCase):
    """Test cases for the SupabaseRepository class"""

    def setUp(self):
        """Set up test fixtures"""
        # Patch the supabase client creation
        self.patcher = patch('myapp.internal.adapters.postgres.supabase_repository.create_client')
        self.mock_create_client = self.patcher.start()
        
        # Create mock client
        self.mock_client = MagicMock()
        self.mock_create_client.return_value = self.mock_client
        
        # Create mock table
        self.mock_table = MagicMock()
        self.mock_client.table.return_value = self.mock_table
        
        # Initialize repository
        self.repository = SupabaseRepository()
        
        # Sample user data
        self.sample_user_data = {
            "id": "user-id-123",
            "email": "test@example.com",
            "name": "Test User",
            "password_hash": "hashed_password:salt",
            "is_verified": True
        }
        
        # Sample document data
        self.sample_document_data = {
            "id": "doc-id-123",
            "user_id": "user-id-123",
            "document_name": "Test Document",
            "document_number": "DOC-123",
            "operation_type": "Test",
            "file_path": "/path/to/document.pdf",
            "file_size_kb": 150,
            "created_at": datetime.now().isoformat(),
            "is_public": False
        }

    def tearDown(self):
        """Clean up after tests"""
        self.patcher.stop()

    def test_create_user_success(self):
        """Test successful user creation"""
        # Configure mock response
        mock_execute = MagicMock()
        mock_execute.data = [self.sample_user_data]
        mock_execute.error = None
        self.mock_table.insert.return_value.execute.return_value = mock_execute
        
        # Mock get_user_by_email to return None (user doesn't exist)
        self.repository.get_user_by_email = MagicMock(return_value=None)
        
        # Call method under test
        result = self.repository.create_user("test@example.com", "Test User", "password123")
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["user"], self.sample_user_data)
        self.mock_table.insert.assert_called_once()
        self.repository.get_user_by_email.assert_called_once_with("test@example.com")

    def test_create_user_existing_email(self):
        """Test user creation with existing email"""
        # Mock get_user_by_email to return a user (email exists)
        existing_user = User.from_dict(self.sample_user_data)
        self.repository.get_user_by_email = MagicMock(return_value=existing_user)
        
        # Call method under test
        result = self.repository.create_user("test@example.com", "Test User", "password123")
        
        # Assertions
        self.assertIn("error", result)
        self.assertEqual(result["error"], "User with this email already exists")
        self.repository.get_user_by_email.assert_called_once_with("test@example.com")
        self.mock_table.insert.assert_not_called()

    def test_get_user_by_email(self):
        """Test retrieving user by email"""
        # Configure mock response
        mock_execute = MagicMock()
        mock_execute.data = [self.sample_user_data]
        self.mock_table.select.return_value.eq.return_value.execute.return_value = mock_execute
        
        # Call method under test
        user = self.repository.get_user_by_email("test@example.com")
        
        # Assertions
        self.assertIsInstance(user, User)
        self.assertEqual(user.id, self.sample_user_data["id"])
        self.assertEqual(user.email, self.sample_user_data["email"])
        self.mock_table.select.assert_called_once_with("*")
        self.mock_table.select.return_value.eq.assert_called_once_with("email", "test@example.com")

    def test_get_user_by_email_not_found(self):
        """Test retrieving user by email when not found"""
        # Configure mock response
        mock_execute = MagicMock()
        mock_execute.data = []
        self.mock_table.select.return_value.eq.return_value.execute.return_value = mock_execute
        
        # Call method under test
        user = self.repository.get_user_by_email("nonexistent@example.com")
        
        # Assertions
        self.assertIsNone(user)
        self.mock_table.select.assert_called_once_with("*")
        self.mock_table.select.return_value.eq.assert_called_once_with("email", "nonexistent@example.com")

    @patch('myapp.internal.adapters.postgres.supabase_repository.SupabaseRepository._verify_password')
    def test_authenticate_user_success(self, mock_verify_password):
        """Test successful user authentication"""
        # Configure mocks
        user = User.from_dict(self.sample_user_data)
        self.repository.get_user_by_email = MagicMock(return_value=user)
        mock_verify_password.return_value = True
        
        # Call method under test
        result = self.repository.authenticate_user("test@example.com", "correct_password")
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["user"]["email"], "test@example.com")
        self.repository.get_user_by_email.assert_called_once_with("test@example.com")
        mock_verify_password.assert_called_once_with(user.password_hash, "correct_password")

    @patch('myapp.internal.adapters.postgres.supabase_repository.SupabaseRepository._verify_password')
    def test_authenticate_user_wrong_password(self, mock_verify_password):
        """Test authentication with wrong password"""
        # Configure mocks
        user = User.from_dict(self.sample_user_data)
        self.repository.get_user_by_email = MagicMock(return_value=user)
        mock_verify_password.return_value = False
        
        # Call method under test
        result = self.repository.authenticate_user("test@example.com", "wrong_password")
        
        # Assertions
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Invalid password")
        self.repository.get_user_by_email.assert_called_once_with("test@example.com")
        mock_verify_password.assert_called_once_with(user.password_hash, "wrong_password")

    def test_save_document(self):
        """Test saving document"""
        # Configure mock response
        mock_execute = MagicMock()
        mock_execute.data = [self.sample_document_data]
        self.mock_table.insert.return_value.execute.return_value = mock_execute
        
        # Mock user check
        sample_user = User.from_dict(self.sample_user_data)
        self.repository.get_user_by_id = MagicMock(return_value=sample_user)
        
        # Prepare document data
        document_data = {
            "document_name": "Test Document",
            "document_number": "DOC-123",
            "operation_type": "Test",
            "file_path": "/path/to/document.pdf",
            "file_size_kb": 150
        }
        
        # Call method under test
        result = self.repository.save_document("user-id-123", document_data)
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["document"], self.sample_document_data)
        self.mock_table.insert.assert_called_once()
        self.repository.get_user_by_id.assert_called_once_with("user-id-123")

    def test_get_user_documents(self):
        """Test retrieving user documents"""
        # Configure mock response
        mock_execute = MagicMock()
        mock_execute.data = [self.sample_document_data]
        self.mock_table.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_execute
        
        # Call method under test
        documents = self.repository.get_user_documents("user-id-123")
        
        # Assertions
        self.assertEqual(len(documents), 1)
        self.assertIsInstance(documents[0], Document)
        self.assertEqual(documents[0].id, self.sample_document_data["id"])
        self.assertEqual(documents[0].document_name, self.sample_document_data["document_name"])
        self.mock_table.select.assert_called_once_with("*")
        self.mock_table.select.return_value.eq.assert_called_once_with("user_id", "user-id-123")


if __name__ == '__main__':
    unittest.main() 