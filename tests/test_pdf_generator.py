import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
import sys
from myapp.internal.adapters.pdf_generator import PDFGeneratorAdapter


class TestPDFGeneratorAdapter(unittest.TestCase):
    """Test cases for the PDFGeneratorAdapter class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary static folder path for testing
        self.test_static_folder = "/tmp/test_static"
        
        # Sample HTML content
        self.html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Document</title>
        </head>
        <body>
            <h1>Test Document</h1>
            <p>This is a test document for PDF generation.</p>
        </body>
        </html>
        """
        
        # Sample document ID
        self.document_id = "test-doc-id"

    @patch('os.path.exists')
    def test_init_without_wkhtmltopdf(self, mock_exists):
        """Test initialization without wkhtmltopdf"""
        # Configure mock
        mock_exists.return_value = False
        
        # Initialize adapter
        adapter = PDFGeneratorAdapter(
            static_folder=self.test_static_folder,
            wkhtmltopdf_path="/path/to/nonexistent/wkhtmltopdf"
        )
        
        # Assertions
        self.assertEqual(adapter.static_folder, self.test_static_folder)
        self.assertEqual(adapter.wkhtmltopdf_path, "/path/to/nonexistent/wkhtmltopdf")
        self.assertEqual(adapter.pdf_renderer, "fallback")

    @patch('os.path.exists')
    def test_init_with_wkhtmltopdf(self, mock_exists):
        """Test initialization with wkhtmltopdf"""
        # Configure mock
        mock_exists.return_value = True
        
        # Initialize adapter
        adapter = PDFGeneratorAdapter(
            static_folder=self.test_static_folder,
            wkhtmltopdf_path="/path/to/wkhtmltopdf"
        )
        
        # Assertions
        self.assertEqual(adapter.static_folder, self.test_static_folder)
        self.assertEqual(adapter.wkhtmltopdf_path, "/path/to/wkhtmltopdf")
        self.assertEqual(adapter.pdf_renderer, "wkhtmltopdf")

    @patch('os.path.exists')
    @patch('pdfkit.from_string')
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_pdf_with_wkhtmltopdf(self, mock_file, mock_pdfkit, mock_exists):
        """Test PDF generation with wkhtmltopdf"""
        # Configure mocks
        mock_exists.return_value = True
        mock_pdfkit.return_value = b"PDF content"
        
        # Initialize adapter
        adapter = PDFGeneratorAdapter(
            static_folder=self.test_static_folder,
            wkhtmltopdf_path="/path/to/wkhtmltopdf"
        )
        
        # Call method under test
        pdf_bytes, pdf_path = adapter.generate_pdf_from_html(self.html_content, self.document_id)
        
        # Assertions
        self.assertEqual(pdf_bytes, b"PDF content")
        self.assertEqual(pdf_path, os.path.join(self.test_static_folder, f"document_{self.document_id}.pdf"))
        mock_pdfkit.assert_called_once()
        mock_file.assert_called_once_with(pdf_path, 'wb')
        mock_file().write.assert_called_once_with(b"PDF content")

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_pdf_fallback(self, mock_file, mock_exists):
        """Test PDF generation with fallback method"""
        # Configure mocks
        mock_exists.return_value = False
        
        # Initialize adapter
        adapter = PDFGeneratorAdapter(
            static_folder=self.test_static_folder,
            wkhtmltopdf_path="/path/to/nonexistent/wkhtmltopdf"
        )
        
        # Call method under test
        pdf_bytes, pdf_path = adapter.generate_pdf_from_html(self.html_content, self.document_id)
        
        # Assertions
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertEqual(pdf_path, os.path.join(self.test_static_folder, f"document_{self.document_id}.html"))
        # Check that the HTML file was opened for writing
        mock_file.assert_any_call(pdf_path, 'w', encoding='utf-8')
        # Check that the HTML content contains our original HTML
        write_calls = mock_file().write.call_args_list
        html_written = False
        for call in write_calls:
            if self.html_content in call[0][0]:
                html_written = True
                break
        self.assertTrue(html_written, "HTML content was not written to file")


if __name__ == '__main__':
    unittest.main() 