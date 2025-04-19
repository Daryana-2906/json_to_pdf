import os
import uuid
import re
from flask import Blueprint, render_template, request, redirect, url_for, send_file, session, flash, jsonify
from werkzeug.utils import secure_filename

from myapp.application.services import UserService, DocumentService
from myapp.domain.models import User, Document

# Create blueprints for different routes
main_routes = Blueprint('main', __name__)
auth_routes = Blueprint('auth', __name__)
document_routes = Blueprint('document', __name__)
api_routes = Blueprint('api', __name__)

# Store services as global variables for easy access in route handlers
user_service = None
document_service = None

# Белый список доступных шаблонов PDF
ALLOWED_PDF_TEMPLATES = {
    'default': 'Стандартный шаблон',
    'formation': 'Образование отходов',
    'transportation': 'Транспортировка отходов',
    'utilization': 'Утилизация отходов',
    'simple': 'Упрощенный шаблон'
}


def init_routes(user_svc: UserService, doc_svc: DocumentService):
    """Initialize route handlers with services"""
    global user_service, document_service
    user_service = user_svc
    document_service = doc_svc


# Main routes
@main_routes.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@main_routes.route('/profile')
def profile():
    """User profile page"""
    if 'user' not in session:
        return redirect(url_for('auth.login', next=request.url))
        
    return render_template('profile.html', user=session['user'])


@main_routes.route('/settings')
def settings():
    """Settings page"""
    if 'user' not in session:
        return redirect(url_for('auth.login', next=request.url))
        
    return render_template('settings.html')


@main_routes.route('/help')
def help_page():
    """Help page"""
    return render_template('help.html')


# Authentication routes
@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handling"""
    if request.method == 'POST':
        # Check format of incoming data
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            next_url = data.get('next', '/')
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            next_url = request.form.get('next', '/')
        
        if not email or not password:
            if request.is_json:
                return jsonify({'error': 'Please enter email and password'})
            flash('Please enter email and password', 'error')
            return redirect(url_for('auth.login', next=next_url))
        
        # Authenticate user
        result = user_service.authenticate_user(email, password)
        
        if result.get('error'):
            if request.is_json:
                return jsonify({'error': result['error']})
            flash(result['error'], 'error')
            return redirect(url_for('auth.login', next=next_url))
        
        # Save user in session
        user_data = result['user']
        session['user'] = {
            'id': user_data.id,
            'name': user_data.name,
            'email': user_data.email,
            'avatar': user_data.avatar_url
        }
        
        if request.is_json:
            return jsonify({'success': True, 'redirect': next_url})
        return redirect(next_url)
    
    # For GET requests show the form
    next_url = request.args.get('next', '/')
    return render_template('login.html', next=next_url)


@auth_routes.route('/register', methods=['POST'])
def register():
    """Handle user registration"""
    # Check format of incoming data
    if request.is_json:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
    else:
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
    
    # Check inputs
    if not all([name, email, password, confirm_password]):
        if request.is_json:
            return jsonify({'error': 'Please fill in all fields'})
        flash('Please fill in all fields', 'error')
        return redirect(url_for('auth.login'))
    
    if password != confirm_password:
        if request.is_json:
            return jsonify({'error': 'Passwords do not match'})
        flash('Passwords do not match', 'error')
        return redirect(url_for('auth.login'))
    
    if len(password) < 8:
        if request.is_json:
            return jsonify({'error': 'Password must be at least 8 characters'})
        flash('Password must be at least 8 characters', 'error')
        return redirect(url_for('auth.login'))
    
    # Create user
    result = user_service.create_user(email, name, password)
    
    if result.get('error'):
        if request.is_json:
            return jsonify({'error': result['error']})
        flash(result['error'], 'error')
        return redirect(url_for('auth.login'))
    
    # Auto-login after registration
    user_data = result['user']
    session['user'] = {
        'id': user_data['id'],
        'name': user_data['name'],
        'email': user_data['email'],
        'avatar': user_data.get('avatar_url')
    }
    
    if request.is_json:
        return jsonify({'success': True, 'redirect': '/'})
    flash('Registration successful!', 'success')
    return redirect(url_for('main.index'))


@auth_routes.route('/logout')
def logout():
    """Logout user"""
    session.pop('user', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('main.index'))


@auth_routes.route('/update_profile', methods=['POST'])
def update_profile():
    """Update user profile"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user']['id']
    
    # Get data for update
    if request.is_json:
        data = request.get_json()
    else:
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email')
        }
        
        # Handle file upload
        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file and avatar_file.filename:
                filename = secure_filename(avatar_file.filename)
                ext = os.path.splitext(filename)[1]
                new_filename = f"avatar_{user_id}_{uuid.uuid4().hex}{ext}"
                
                # Save file
                uploads_dir = os.path.join(os.getcwd(), 'static', 'uploads')
                if not os.path.exists(uploads_dir):
                    os.makedirs(uploads_dir)
                    
                file_path = os.path.join(uploads_dir, new_filename)
                avatar_file.save(file_path)
                
                # Update avatar URL
                data['avatar_url'] = f"/static/uploads/{new_filename}"
    
    # Update profile
    result = user_service.update_profile(user_id, data)
    
    if result.get('error'):
        if request.is_json:
            return jsonify({'error': result['error']})
        flash(result['error'], 'error')
    else:
        # Update session data
        if 'user' in result:
            user_data = result['user']
            session['user'] = {
                'id': user_data.get('id') or user_id,
                'name': user_data.get('name') or session['user']['name'],
                'email': user_data.get('email') or session['user']['email'],
                'avatar': user_data.get('avatar_url') or session['user'].get('avatar')
            }
        
        if request.is_json:
            return jsonify({'success': True})
        flash('Profile updated successfully', 'success')
    
    return redirect(url_for('main.profile'))


# Document routes
@document_routes.route('/templates')
def templates():
    """Templates page"""
    if 'user' not in session:
        return redirect(url_for('auth.login', next=request.url))
        
    return render_template('templates.html')


@document_routes.route('/documents')
def documents():
    """User documents page"""
    if 'user' not in session:
        return redirect(url_for('auth.login', next=request.url))
        
    user_id = session['user']['id']
    docs = document_service.get_user_documents(user_id)
    
    return render_template('documents.html', documents=docs)


@document_routes.route('/generate', methods=['GET', 'POST'])
def generate():
    """Generate document page and handler"""
    if 'user' not in session:
        return redirect(url_for('auth.login', next=request.url))
        
    if request.method == 'POST':
        user_id = session['user']['id']
        
        # Get form data
        data = request.form.to_dict()
        document_name = data.get('document_name', 'Untitled')
        
        # Валидация имени шаблона по белому списку
        template_name = data.get('template', 'default')
        if template_name not in ALLOWED_PDF_TEMPLATES:
            flash('Выбран недопустимый шаблон документа', 'error')
            return redirect(url_for('document_routes.generate'))
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Generate QR code
        qr_code = document_service.generate_qr_code(document_id)
        
        # Prepare HTML content с проверенным именем шаблона
        template_data = {
            'document_id': document_id,
            'qr_code': qr_code,
            'user': session['user'],
            'data': data
        }
        html_content = render_template(f'pdf/{template_name}.html', **template_data)
        
        # Generate PDF
        pdf_bytes, pdf_path = document_service.generate_pdf(html_content, document_id)
        
        # Save document information
        document_data = {
            'document_name': document_name,
            'document_number': data.get('document_number'),
            'operation_type': data.get('operation_type', 'Other'),
            'file_path': pdf_path,
            'file_size_kb': len(pdf_bytes) // 1024,
            'content': data
        }
        result = document_service.save_document(user_id, document_data)
        
        if result.get('error'):
            flash(result['error'], 'error')
            return redirect(url_for('document_routes.generate'))
            
        # Success - offer download
        return render_template('download.html', document=result['document'])
    
    # При GET-запросе передаем список доступных шаблонов
    return render_template('generate.html', templates=ALLOWED_PDF_TEMPLATES)


# API routes
@api_routes.route('/login', methods=['POST'])
def api_login():
    """API login endpoint"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
        
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
        
    result = user_service.authenticate_user(email, password)
    
    if result.get('error'):
        return jsonify({'error': result['error']}), 401
        
    # Success
    user_data = result['user']
    return jsonify({
        'success': True,
        'user': {
            'id': user_data.id,
            'name': user_data.name,
            'email': user_data.email
        }
    })


@api_routes.route('/profile', methods=['GET'])
def api_profile():
    """API profile endpoint"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    user_id = session['user']['id']
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'avatar': user.avatar_url
    })


@api_routes.route('/documents', methods=['GET'])
def api_documents():
    """API documents endpoint"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    user_id = session['user']['id']
    docs = document_service.get_user_documents(user_id)
    
    docs_list = []
    for doc in docs:
        docs_list.append({
            'id': doc.id,
            'name': doc.document_name,
            'document_number': doc.document_number,
            'operation_type': doc.operation_type,
            'created_at': doc.created_at
        })
        
    return jsonify(docs_list) 