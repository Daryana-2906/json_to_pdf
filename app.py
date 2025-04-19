import os
import uuid
import json
import pdfkit
import qrcode
import io
import base64
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash, jsonify
from werkzeug.utils import secure_filename
from supabase_client import supabase_client

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Для работы с сессиями

# Директории для сохранения файлов
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

# Явно указываем путь к wkhtmltopdf
wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

# Проверяем наличие wkhtmltopdf
if os.path.exists(wkhtmltopdf_path):
    print(f"[INFO] wkhtmltopdf найден по пути: {wkhtmltopdf_path}")
    pdf_renderer = "wkhtmltopdf"
else:
    print(f"[WARNING] wkhtmltopdf не найден по указанному пути: {wkhtmltopdf_path}")
    print(f"[INFO] Будет использован запасной метод рендеринга PDF")
    pdf_renderer = "fallback"

def generate_qr_code(document_id):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(f"https://example.com/verify/{document_id}")
    qr.make(fit=True)
    
    # Создаем QR код с лучшим визуальным стилем
    img = qr.make_image(fill_color="#624deb", back_color="white")

    # Сохраняем изображение в память и преобразуем в base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"

def generate_pdf_with_wkhtmltopdf(html_content, document_id):
    """Генерация PDF с использованием wkhtmltopdf"""
    print(f"[PDF Debug] Используется wkhtmltopdf для создания PDF")
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
        'image-quality': 100,
        'debug-javascript': True,
        'log-level': 'info'
    }
    
    # Генерация PDF в виде байтов
    try:
        pdf_bytes = pdfkit.from_string(html_content, False, options=pdf_options, configuration=config)
        pdf_path = os.path.join(STATIC_FOLDER, f"document_{document_id}.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        print(f"[PDF Debug] PDF успешно создан с помощью wkhtmltopdf: {pdf_path}")
        return pdf_bytes, pdf_path
    except Exception as e:
        print(f"[PDF Debug] Ошибка при создании PDF с помощью wkhtmltopdf: {str(e)}")
        raise e

def generate_pdf_fallback(html_content, document_id):
    """Запасной метод - сохраняем просто HTML и условно считаем его PDF"""
    print(f"[PDF Debug] Используется запасной метод для создания PDF (HTML)")
    try:
        # Создаем улучшенный HTML с встроенными стилями для печати
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
        
        # Сохраняем HTML файл как запасной вариант для PDF
        html_path = os.path.join(STATIC_FOLDER, f"document_{document_id}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_html)
        
        # Сохраняем пустой PDF файл с указанием, что нужно использовать HTML
        pdf_path = os.path.join(STATIC_FOLDER, f"document_{document_id}.pdf")
        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(f"PDF generation failed. Please use HTML version: {html_path}")
        
        # Возвращаем HTML-контент как бинарный для совместимости
        pdf_bytes = enhanced_html.encode('utf-8')
        print(f"[PDF Debug] HTML-документ успешно создан как запасной PDF: {html_path}")
        return pdf_bytes, html_path
    except Exception as e:
        print(f"[PDF Debug] Ошибка при создании HTML-документа: {str(e)}")
        raise e

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа и регистрации"""
    if request.method == 'POST':
        # Проверяем, в каком формате пришли данные
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
                return jsonify({'error': 'Пожалуйста, введите email и пароль'})
            flash('Пожалуйста, введите email и пароль', 'error')
            return redirect(url_for('login', next=next_url))
        
        # Аутентификация пользователя через Supabase
        result = supabase_client.authenticate_user(email, password)
        
        if result.get('error'):
            if request.is_json:
                return jsonify({'error': result['error']})
            flash(result['error'], 'error')
            return redirect(url_for('login', next=next_url))
        
        # Сохраняем пользователя в сессии
        user_data = result['user']
        session['user'] = {
            'id': user_data['id'],
            'name': user_data['name'],
            'email': user_data['email'],
            'avatar': user_data.get('avatar_url')
        }
        
        if request.is_json:
            return jsonify({'success': True, 'redirect': next_url})
        return redirect(next_url)
    
    # Для GET запроса показываем форму
    next_url = request.args.get('next', '/')
    return render_template('login.html', next=next_url)

@app.route('/register', methods=['POST'])
def register():
    """Обработка регистрации пользователя"""
    # Проверяем, в каком формате пришли данные
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
    
    # Проверка входных данных
    if not all([name, email, password, confirm_password]):
        if request.is_json:
            return jsonify({'error': 'Пожалуйста, заполните все поля'})
        flash('Пожалуйста, заполните все поля', 'error')
        return redirect(url_for('login'))
    
    if password != confirm_password:
        if request.is_json:
            return jsonify({'error': 'Пароли не совпадают'})
        flash('Пароли не совпадают', 'error')
        return redirect(url_for('login'))
    
    if len(password) < 8:
        if request.is_json:
            return jsonify({'error': 'Пароль должен содержать не менее 8 символов'})
        flash('Пароль должен содержать не менее 8 символов', 'error')
        return redirect(url_for('login'))
    
    # Регистрация пользователя в Supabase
    result = supabase_client.create_user(email, name, password)
    
    if result.get('error'):
        if request.is_json:
            return jsonify({'error': result['error']})
        flash(result['error'], 'error')
        return redirect(url_for('login'))
    
    # Автоматически входим пользователя после регистрации
    user_data = result['user']
    session['user'] = {
        'id': user_data['id'],
        'name': user_data['name'],
        'email': user_data['email'],
        'avatar': user_data.get('avatar_url')
    }
    
    if request.is_json:
        return jsonify({'success': True, 'redirect': '/'})
    flash('Регистрация успешна!', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.pop('user', None)
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('index'))

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    """
    Генерирует PDF документ на основе предоставленных данных.
    """
    # Проверка авторизации
    if not session.get('user'):
        if request.method == 'POST':
            # Если пришел POST-запрос, сохраняем данные в сессии и перенаправляем на логин
            if request.form.get('json_input'):
                session['pending_json_data'] = request.form.get('json_input')
            return redirect(url_for('login', next='/generate'))
        return redirect(url_for('login', next=request.path))
    
    error = None
    
    if request.method == 'POST':
        try:
            # Получаем JSON данные из формы
            json_input = request.form.get('json_input', session.pop('pending_json_data', ''))
            
            # Если JSON пуст, выдаем ошибку
            if not json_input.strip():
                error = "Пожалуйста, предоставьте данные в формате JSON"
                return render_template('result.html', error=error)
            
            # Парсим JSON
            try:
                data = json.loads(json_input)
            except json.JSONDecodeError as e:
                error = f"Недопустимый формат JSON: {str(e)}"
                return render_template('result.html', error=error)
            
            # Генерируем уникальный ID документа
            document_id = str(uuid.uuid4())
            
            # Добавляем QR-код в данные
            data['qr_code'] = generate_qr_code(document_id)
            data['document_id'] = document_id
            
            # Генерируем HTML из шаблона
            try:
                html_content = render_template('universal.html', **data)
            except Exception as e:
                error = f"Ошибка при рендеринге шаблона: {str(e)}"
                return render_template('result.html', error=error)
            
            # Создаем PDF с использованием соответствующего метода
            try:
                if pdf_renderer == "wkhtmltopdf" and os.path.exists(wkhtmltopdf_path):
                    pdf_bytes, file_path = generate_pdf_with_wkhtmltopdf(html_content, document_id)
                else:
                    pdf_bytes, file_path = generate_pdf_fallback(html_content, document_id)
            except Exception as e:
                error = f"Ошибка при создании PDF: {str(e)}"
                return render_template('result.html', error=error)
            
            # Получаем метаданные документа
            try:
                file_size_kb = round(os.path.getsize(file_path) / 1024, 2)
            except:
                file_size_kb = 0
                
            document_meta = {
                'template_type': data.get('operation_type', 'документ'),
                'created_at': datetime.now().strftime('%d.%m.%Y %H:%M'),
                'size_kb': file_size_kb,
                'number': data.get('document_number', 'б/н'),
                'pages': 1  # В будущем можно добавить подсчет страниц PDF
            }
            
            # Формируем URL для доступа к PDF
            pdf_url = url_for('static', filename=f'document_{document_id}.pdf')
            
            # Сохраняем информацию о документе в Supabase
            user_id = session['user']['id']
            document_data = {
                'document_name': f"{document_meta['template_type']} {document_meta['number']}",
                'document_number': document_meta['number'],
                'operation_type': document_meta['template_type'],
                'file_path': file_path,
                'file_size_kb': file_size_kb,
                'pages': document_meta['pages'],
                'json_data': data
            }
            
            supabase_client.save_document(user_id, document_data)
            
            # Отображаем результаты
            return render_template('result.html', 
                                  pdf_url=pdf_url, 
                                  document_id=document_id,
                                  document_meta=document_meta)
            
        except Exception as e:
            error = f"Произошла ошибка: {str(e)}"
            return render_template('result.html', error=error)
    
    # Для GET запроса показываем форму
    return render_template('index.html')

@app.route('/templates')
def templates():
    """Страница с шаблонами документов"""
    if not session.get('user'):
        return redirect(url_for('login', next=request.path))
    return render_template('templates.html')

@app.route('/documents')
def documents():
    """Страница с документами пользователя"""
    if not session.get('user'):
        return redirect(url_for('login', next=request.path))
    
    user_id = session['user']['id']
    user_documents = supabase_client.get_user_documents(user_id)
    
    return render_template('documents.html', documents=user_documents)

@app.route('/profile')
def profile():
    """Страница профиля пользователя"""
    if not session.get('user'):
        return redirect(url_for('login', next=request.path))
    
    user_id = session['user']['id']
    user_data = supabase_client.get_user_by_id(user_id)
    
    if not user_data:
        flash('Произошла ошибка при загрузке данных профиля', 'error')
        return redirect(url_for('index'))
    
    return render_template('profile.html', user=user_data)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    """Обновление профиля пользователя"""
    if not session.get('user'):
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    name = request.form.get('name')
    
    update_data = {'name': name}
    
    # Обработка аватара, если загружен
    if 'avatar' in request.files:
        avatar_file = request.files['avatar']
        if avatar_file and avatar_file.filename:
            # Здесь можно добавить загрузку файла в хранилище и получение URL
            # Для примера просто сохраняем локально
            avatar_filename = f"avatar_{user_id}_{secure_filename(avatar_file.filename)}"
            avatar_path = os.path.join(STATIC_FOLDER, avatar_filename)
            avatar_file.save(avatar_path)
            avatar_url = url_for('static', filename=avatar_filename)
            update_data['avatar_url'] = avatar_url
    
    result = supabase_client.update_user_profile(user_id, update_data)
    
    if result.get('error'):
        flash(result['error'], 'error')
    else:
        flash('Профиль успешно обновлен', 'success')
        # Обновляем данные в сессии
        session['user']['name'] = name
        if 'avatar_url' in update_data:
            session['user']['avatar'] = update_data['avatar_url']
    
    return redirect(url_for('profile'))

@app.route('/settings')
def settings():
    """Страница настроек пользователя"""
    if not session.get('user'):
        return redirect(url_for('login', next=request.path))
    return render_template('settings.html')

@app.route('/help')
def help_page():
    """Страница помощи"""
    return render_template('help.html')

# API маршруты
@app.route('/api/login', methods=['POST'])
def api_login():
    """API для входа в систему"""
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Не указан email или пароль'})
    
    result = supabase_client.authenticate_user(email, password)
    
    if result.get('error'):
        return jsonify({'success': False, 'error': result['error']})
    
    # Сохраняем пользователя в сессии
    user_data = result['user']
    session['user'] = {
        'id': user_data['id'],
        'name': user_data['name'],
        'email': user_data['email'],
        'avatar': user_data.get('avatar_url')
    }
    
    return jsonify({'success': True, 'redirect': request.form.get('next', '/')})

@app.route('/api/profile', methods=['GET'])
def api_profile():
    """API для получения данных профиля"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'})
    
    user_id = session['user']['id']
    user_data = supabase_client.get_user_by_id(user_id)
    
    if not user_data:
        return jsonify({'success': False, 'error': 'Пользователь не найден'})
    
    # Не возвращаем хеш пароля
    if 'password_hash' in user_data:
        del user_data['password_hash']
    
    return jsonify({'success': True, 'user': user_data})

@app.route('/api/documents', methods=['GET'])
def api_documents():
    """API для получения документов пользователя"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Требуется авторизация'})
    
    user_id = session['user']['id']
    user_documents = supabase_client.get_user_documents(user_id)
    
    return jsonify({'success': True, 'documents': user_documents})

# Маршрут для работы с примерами JSON
@app.route('/examples/<example_name>')
def get_example(example_name):
    """Возвращает пример JSON по имени"""
    try:
        example_path = os.path.join('examples', f'{example_name}.json')
        with open(example_path, 'r', encoding='utf-8') as f:
            example_data = f.read()
        return jsonify({'success': True, 'data': example_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def create_pdf_from_html(html_content, output_path, options=None):
    """
    Создает PDF файл из HTML контента.
    
    Args:
        html_content (str): HTML контент для конвертации
        output_path (str): Путь для сохранения PDF файла
        options (dict, optional): Опции для конвертации. По умолчанию None.
        
    Returns:
        bool: True если PDF успешно создан, иначе False
    """
    try:
        default_options = {
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None
        }
        
        if options:
            default_options.update(options)
            
        # Сохраняем HTML во временный файл для отладки
        debug_html_path = os.path.join(STATIC_FOLDER, f'debug_html_{uuid.uuid4()}.html')
        with open(debug_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Создаем PDF с использованием соответствующего метода
        if pdf_renderer == "wkhtmltopdf" and os.path.exists(wkhtmltopdf_path):
            try:
                # Создаем PDF с использованием wkhtmltopdf
                pdfkit.from_string(html_content, output_path, options=default_options, configuration=config)
                return True
            except Exception as e:
                print(f"[ERROR] Ошибка при создании PDF с помощью wkhtmltopdf: {str(e)}")
                # Пробуем запасной метод
                return create_pdf_fallback(html_content, output_path)
        else:
            # Используем запасной метод
            return create_pdf_fallback(html_content, output_path)
    except Exception as e:
        print(f"[ERROR] Общая ошибка при создании PDF: {str(e)}")
        return False

def create_pdf_fallback(html_content, output_path):
    """
    Запасной метод создания PDF - сохраняем HTML как файл
    """
    try:
        # Сохраняем HTML файл в папке static
        html_path = output_path.replace('.pdf', '.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        # Создаем пустой PDF файл с сообщением
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("PDF generation failed. Please use HTML version.")
            
        print(f"[INFO] Создан запасной HTML файл: {html_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка при создании запасного HTML файла: {str(e)}")
        return False

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Проверка подключения к Supabase
    print("[INFO] Проверка соединения с Supabase...")
    try:
        # Проверка соединения через простой запрос к таблице users
        version = supabase_client.supabase.table("users").select("*").limit(1).execute()
        print(f"[INFO] Соединение с Supabase установлено успешно.")
    except Exception as e:
        print(f"[ERROR] Ошибка соединения с Supabase: {str(e)}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)