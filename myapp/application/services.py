import hashlib
import uuid
import os
import pdfkit
import qrcode
import io
import base64
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Tuple

from myapp.domain.repositories import UserRepository, DocumentRepository
from myapp.domain.models import User, Document


class UserService:
    """Service for user-related operations"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        
    def _hash_password(self, password: str) -> str:
        """Hash a password"""
        salt = uuid.uuid4().hex
        return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt
        
    def _verify_password(self, hashed_password: str, provided_password: str) -> bool:
        """Verify a password against a hash"""
        password, salt = hashed_password.split(':')
        return password == hashlib.sha256(salt.encode() + provided_password.encode()).hexdigest()
        
    def create_user(self, email: str, name: str, password: str) -> Dict[str, Any]:
        """Create a new user"""
        # Check if user exists
        existing_user = self.user_repository.get_user_by_email(email)
        if existing_user:
            return {"error": "Пользователь с таким email уже существует"}
            
        # Hash password
        password_hash = self._hash_password(password)
        
        # Create user
        result = self.user_repository.create_user(email, name, password_hash)
        return result
        
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate a user"""
        user = self.user_repository.get_user_by_email(email)
        
        if not user:
            return {"error": "Пользователь не найден"}
            
        if not self._verify_password(user.password_hash, password):
            return {"error": "Неверный пароль"}
            
        return {"success": True, "user": user}
        
    def update_profile(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        return self.user_repository.update_user_profile(user_id, update_data)


class DocumentService:
    """Service for document-related operations"""
    
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository
        self.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'static')
        if not os.path.exists(self.static_folder):
            os.makedirs(self.static_folder)
        
        # Setup PDF configuration
        self.wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        self.config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)
        
    def generate_qr_code(self, document_id: str) -> str:
        """Generate QR code for a document"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(f"https://example.com/verify/{document_id}")
        qr.make(fit=True)
        
        # Create QR code with better visual style
        img = qr.make_image(fill_color="#624deb", back_color="white")

        # Save image to memory and convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"
        
    def generate_pdf(self, html_content: str, document_id: str) -> Tuple[bytes, str]:
        """Generate PDF from HTML content"""
        if os.path.exists(self.wkhtmltopdf_path):
            return self._generate_pdf_with_wkhtmltopdf(html_content, document_id)
        else:
            return self._generate_pdf_fallback(html_content, document_id)
            
    def _generate_pdf_with_wkhtmltopdf(self, html_content: str, document_id: str) -> Tuple[bytes, str]:
        """Generate PDF using wkhtmltopdf"""
        pdf_options = {
            'encoding': 'UTF-8',
            'page-size': 'A4',
            'margin-top': '10mm',
            'margin-right': '10mm',
            'margin-bottom': '10mm',
            'margin-left': '10mm',
            'enable-local-file-access': True,
            'print-media-type': True,
            'dpi': 300,
            'javascript-delay': 1000,
            'no-stop-slow-scripts': True,
            'image-quality': 100
        }
        
        # Generate PDF bytes
        pdf_bytes = pdfkit.from_string(html_content, False, options=pdf_options, configuration=self.config)
        pdf_path = os.path.join(self.static_folder, f"document_{document_id}.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        return pdf_bytes, pdf_path
        
    def _generate_pdf_fallback(self, html_content: str, document_id: str) -> Tuple[bytes, str]:
        """Fallback method - save HTML and consider it as PDF"""
        enhanced_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Document {document_id}</title>
    <style>
        @media print {{
            body {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
        }}
    </style>
</head>
<body>
    {html_content}
    <script>
        window.onload = function() {{
            // Auto-print when loaded in a new window
            if (window.opener) {{
                window.print();
            }}
        }};
    </script>
</body>
</html>"""
        
        # Save HTML file as backup for PDF
        html_path = os.path.join(self.static_folder, f"document_{document_id}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_html)
            
        # Return HTML content as binary for compatibility
        pdf_bytes = enhanced_html.encode('utf-8')
        return pdf_bytes, html_path
        
    def save_document(self, user_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save document information"""
        return self.document_repository.save_document(user_id, document_data)
        
    def get_user_documents(self, user_id: str) -> List[Document]:
        """Get all documents for a user"""
        return self.document_repository.get_user_documents(user_id)
        
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """Get a document by ID"""
        return self.document_repository.get_document_by_id(document_id) 