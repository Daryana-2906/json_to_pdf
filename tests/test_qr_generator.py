import unittest
from unittest.mock import MagicMock, patch
import base64
from io import BytesIO
from myapp.internal.adapters.qr_generator import QRCodeGeneratorAdapter


class TestQRCodeGeneratorAdapter(unittest.TestCase):
    """Test cases for the QRCodeGeneratorAdapter class"""

    def setUp(self):
        """Set up test fixtures"""
        self.verification_url_base = "https://example.com/verify/"
        self.document_id = "test-doc-id"
        self.qr_generator = QRCodeGeneratorAdapter(verification_url_base=self.verification_url_base)

    def test_initialization(self):
        """Test initialization of QR code generator"""
        self.assertEqual(self.qr_generator.verification_url_base, self.verification_url_base)

    @patch('qrcode.QRCode')
    def test_generate_qr_code(self, mock_qrcode_class):
        """Test QR code generation"""
        # Create mock QR code
        mock_qrcode = MagicMock()
        mock_qrcode_class.return_value = mock_qrcode
        
        # Mock the image generation
        mock_img = MagicMock()
        mock_qrcode.make_image.return_value = mock_img
        
        # Mock the save method to write test data to buffer
        def mock_save_to_buffer(buffer, format):
            buffer.write(b"test_qr_image_data")
        
        mock_img.save.side_effect = mock_save_to_buffer
        
        # Call method under test
        result = self.qr_generator.generate_qr_code(self.document_id)
        
        # Assertions
        mock_qrcode.add_data.assert_called_once_with(f"{self.verification_url_base}{self.document_id}")
        mock_qrcode.make.assert_called_once_with(fit=True)
        mock_qrcode.make_image.assert_called_once_with(fill_color="#624deb", back_color="white")
        
        # Check that the result is a base64 data URL
        self.assertTrue(result.startswith("data:image/png;base64,"))
        
        # Extract and verify base64 content
        base64_content = result.replace("data:image/png;base64,", "")
        decoded_content = base64.b64decode(base64_content)
        self.assertEqual(decoded_content, b"test_qr_image_data")

    def test_generate_qr_code_integration(self):
        """Integration test for QR code generation"""
        # Call method under test
        result = self.qr_generator.generate_qr_code(self.document_id)
        
        # Basic validation
        self.assertTrue(result.startswith("data:image/png;base64,"))
        
        # Extract base64 content and verify it's valid
        base64_content = result.replace("data:image/png;base64,", "")
        try:
            decoded_content = base64.b64decode(base64_content)
            self.assertIsInstance(decoded_content, bytes)
            self.assertTrue(len(decoded_content) > 0)
        except Exception as e:
            self.fail(f"Failed to decode base64 content: {str(e)}")

    def test_generate_qr_code_with_different_url(self):
        """Test QR code generation with different verification URL"""
        # Create generator with different URL
        different_url = "https://different-domain.com/verify-document/"
        generator = QRCodeGeneratorAdapter(verification_url_base=different_url)
        
        # Use mock to check correct URL is used
        with patch('qrcode.QRCode') as mock_qrcode_class:
            mock_qrcode = MagicMock()
            mock_qrcode_class.return_value = mock_qrcode
            
            # Mock the image and save for complete test flow
            mock_img = MagicMock()
            mock_qrcode.make_image.return_value = mock_img
            
            # Mock the save method
            def mock_save_to_buffer(buffer, format):
                buffer.write(b"test_qr_image_data")
            
            mock_img.save.side_effect = mock_save_to_buffer
            
            # Call method under test
            generator.generate_qr_code(self.document_id)
            
            # Verify correct URL was used
            mock_qrcode.add_data.assert_called_once_with(f"{different_url}{self.document_id}")


if __name__ == '__main__':
    unittest.main() 