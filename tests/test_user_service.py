import unittest
from unittest.mock import MagicMock, patch
from myapp.internal.application.user_service import UserService
from myapp.internal.domain.models import User


class TestUserService(unittest.TestCase):
    """Test cases for the UserService class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_repository = MagicMock()
        self.user_service = UserService(self.mock_repository)
        
        # Sample user data
        self.sample_user = User(
            id="test-user-id",
            email="test@example.com",
            name="Test User",
            password_hash="hashed_password:salt",
            is_verified=True
        )
        
        # Sample authentication response
        self.auth_success_response = {
            "success": True,
            "user": self.sample_user.to_dict()
        }
        
        self.auth_failure_response = {
            "error": "Invalid password"
        }

    def test_create_user_success(self):
        """Test successful user creation"""
        # Configure mock
        self.mock_repository.create_user.return_value = {"success": True, "user": self.sample_user.to_dict()}
        
        # Call method under test
        result = self.user_service.create_user("test@example.com", "Test User", "password123")
        
        # Assertions
        self.mock_repository.create_user.assert_called_once_with("test@example.com", "Test User", "password123")
        self.assertTrue(result["success"])
        self.assertEqual(result["user"]["email"], "test@example.com")
        self.assertEqual(result["user"]["name"], "Test User")

    def test_create_user_existing_email(self):
        """Test user creation with existing email"""
        # Configure mock
        self.mock_repository.create_user.return_value = {"error": "User with this email already exists"}
        
        # Call method under test
        result = self.user_service.create_user("existing@example.com", "Test User", "password123")
        
        # Assertions
        self.assertIn("error", result)
        self.assertEqual(result["error"], "User with this email already exists")

    def test_authenticate_user_success(self):
        """Test successful user authentication"""
        # Configure mock
        self.mock_repository.authenticate_user.return_value = self.auth_success_response
        
        # Call method under test
        result = self.user_service.authenticate_user("test@example.com", "correct_password")
        
        # Assertions
        self.mock_repository.authenticate_user.assert_called_once_with("test@example.com", "correct_password")
        self.assertTrue(result["success"])
        self.assertEqual(result["user"]["email"], "test@example.com")

    def test_authenticate_user_failure(self):
        """Test failed user authentication"""
        # Configure mock
        self.mock_repository.authenticate_user.return_value = self.auth_failure_response
        
        # Call method under test
        result = self.user_service.authenticate_user("test@example.com", "wrong_password")
        
        # Assertions
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Invalid password")

    def test_get_user_by_id(self):
        """Test retrieving user by ID"""
        # Configure mock
        self.mock_repository.get_user_by_id.return_value = self.sample_user
        
        # Call method under test
        user = self.user_service.get_user_by_id("test-user-id")
        
        # Assertions
        self.mock_repository.get_user_by_id.assert_called_once_with("test-user-id")
        self.assertIsInstance(user, User)
        self.assertEqual(user.id, "test-user-id")
        self.assertEqual(user.email, "test@example.com")

    def test_get_user_by_email(self):
        """Test retrieving user by email"""
        # Configure mock
        self.mock_repository.get_user_by_email.return_value = self.sample_user
        
        # Call method under test
        user = self.user_service.get_user_by_email("test@example.com")
        
        # Assertions
        self.mock_repository.get_user_by_email.assert_called_once_with("test@example.com")
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, "test@example.com")


if __name__ == '__main__':
    unittest.main() 