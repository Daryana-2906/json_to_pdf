import unittest
from unittest.mock import MagicMock, patch
from myapp.internal.application.document_service import DocumentService
from myapp.internal.domain.models import Document
from datetime import datetime


class TestDocumentService(unittest.TestCase):
    """Test cases for the DocumentService class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_repository = MagicMock()
        self.mock_pdf_generator = MagicMock()
        self.mock_qr_generator = MagicMock()
        
        self.document_service = DocumentService(
            document_repository=self.mock_repository,
            pdf_generator=self.mock_pdf_generator,
            qr_generator=self.mock_qr_generator
        )
        
        # Sample document data
        self.sample_document = Document(
            id="test-doc-id",
            user_id="test-user-id",
            document_name="Test Document",
            document_number="DOC-123",
            operation_type="Test",
            file_path="/path/to/document.pdf",
            file_size_kb=150,
            created_at=datetime.now(),
            is_public=False
        )
        
        # Sample save response
        self.save_success_response = {
            "success": True,
            "document": self.sample_document.to_dict()
        }

    def test_save_document(self):
        """Test saving document"""
        # Configure mock
        self.mock_repository.save_document.return_value = self.save_success_response
        
        document_data = {
            "document_name": "Test Document",
            "document_number": "DOC-123",
            "operation_type": "Test"
        }
        
        # Call method under test
        result = self.document_service.save_document("test-user-id", document_data)
        
        # Assertions
        self.mock_repository.save_document.assert_called_once_with("test-user-id", document_data)
        self.assertTrue(result["success"])
        self.assertEqual(result["document"]["document_name"], "Test Document")

    def test_get_user_documents(self):
        """Test retrieving user documents"""
        # Configure mock
        self.mock_repository.get_user_documents.return_value = [self.sample_document]
        
        # Call method under test
        documents = self.document_service.get_user_documents("test-user-id")
        
        # Assertions
        self.mock_repository.get_user_documents.assert_called_once_with("test-user-id")
        self.assertEqual(len(documents), 1)
        self.assertIsInstance(documents[0], Document)
        self.assertEqual(documents[0].document_name, "Test Document")

    def test_get_document_by_id(self):
        """Test retrieving document by ID"""
        # Configure mock
        self.mock_repository.get_document_by_id.return_value = self.sample_document
        
        # Call method under test
        document = self.document_service.get_document_by_id("test-doc-id")
        
        # Assertions
        self.mock_repository.get_document_by_id.assert_called_once_with("test-doc-id")
        self.assertIsInstance(document, Document)
        self.assertEqual(document.id, "test-doc-id")
        self.assertEqual(document.document_name, "Test Document")

    def test_generate_pdf(self):
        """Test PDF generation"""
        # Configure mock
        pdf_bytes = b"PDF content"
        pdf_path = "/path/to/document.pdf"
        self.mock_pdf_generator.generate_pdf_from_html.return_value = (pdf_bytes, pdf_path)
        
        # Call method under test
        result_bytes, result_path = self.document_service.generate_pdf("<html>Test</html>", "test-doc-id")
        
        # Assertions
        self.mock_pdf_generator.generate_pdf_from_html.assert_called_once_with("<html>Test</html>", "test-doc-id")
        self.assertEqual(result_bytes, pdf_bytes)
        self.assertEqual(result_path, pdf_path)

    def test_generate_qr_code(self):
        """Test QR code generation"""
        # Configure mock
        qr_code_data = "data:image/png;base64,ABC123=="
        self.mock_qr_generator.generate_qr_code.return_value = qr_code_data
        
        # Call method under test
        result = self.document_service.generate_qr_code("test-doc-id")
        
        # Assertions
        self.mock_qr_generator.generate_qr_code.assert_called_once_with("test-doc-id")
        self.assertEqual(result, qr_code_data)

    @patch('uuid.uuid4')
    def test_create_document_from_html(self, mock_uuid):
        """Test document creation from HTML content"""
        # Configure mocks
        mock_uuid.return_value = "test-doc-id"
        
        qr_code_data = "data:image/png;base64,ABC123=="
        self.mock_qr_generator.generate_qr_code.return_value = qr_code_data
        
        pdf_bytes = b"PDF content with QR"
        pdf_path = "/path/to/document.pdf"
        self.mock_pdf_generator.generate_pdf_from_html.return_value = (pdf_bytes, pdf_path)
        
        self.mock_repository.save_document.return_value = self.save_success_response
        
        # Call method under test
        result = self.document_service.create_document_from_html(
            user_id="test-user-id",
            html_content="<html>Test {{QR_CODE}}</html>",
            document_name="Test Document",
            document_number="DOC-123",
            operation_type="Test"
        )
        
        # Assertions
        self.mock_qr_generator.generate_qr_code.assert_called_once_with("test-doc-id")
        
        expected_html = "<html>Test data:image/png;base64,ABC123==</html>"
        self.mock_pdf_generator.generate_pdf_from_html.assert_called_once_with(expected_html, "test-doc-id")
        
        expected_doc_data = {
            "document_name": "Test Document",
            "document_number": "DOC-123",
            "operation_type": "Test",
            "file_path": pdf_path,
            "file_size_kb": 0,  # len(pdf_bytes) // 1024 which is 0 in this case
        }
        self.mock_repository.save_document.assert_called_once()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["document"]["document_name"], "Test Document")


if __name__ == '__main__':
    unittest.main() 