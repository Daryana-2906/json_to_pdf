from flask import Flask, request, send_file, jsonify, render_template, url_for
from jinja2 import Environment, FileSystemLoader
import pdfkit
import qrcode
import io
import os
import uuid
import base64
from io import BytesIO
import json

app = Flask(__name__)
env = Environment(loader=FileSystemLoader('templates'))

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
        pdf_path = f"static/document_{document_id}.pdf"
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
        html_path = f"static/document_{document_id}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_html)
        
        # Сохраняем пустой PDF файл с указанием, что нужно использовать HTML
        pdf_path = f"static/document_{document_id}.pdf"
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
    # Пример JSON для отображения в форме
    example_json = {
        "template": "act.html",
        "document_number": "ACT-001",
        "date": "2025-04-19",
        "wastes": [
            {"name": "Ртутьсодержащие лампы", "hazard_class": "I", "quantity": 10},
            {"name": "Аккумуляторы", "hazard_class": "II", "quantity": 50}
        ],
        "responsible_person": "Иванов И.И."
    }
    return render_template('index.html', example_json=example_json)


@app.route('/generate', methods=['POST'])
def generate():
    json_input = request.form.get('json_input', '').strip()

    # Проверяем, пустой ли JSON
    if not json_input:
        return render_template('result.html', error="JSON не может быть пустым. Пожалуйста, введите корректный JSON.")

    try:
        # Парсим JSON из формы
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        return render_template('result.html', error=f"Ошибка в JSON: {str(e)}")

    template_name = data.get('template', 'act.html')
    if template_name not in ['act.html', 'request.html']:
        return render_template('result.html', error="Неверное имя шаблона. Используйте 'act.html' или 'request.html'.")

    document_id = str(uuid.uuid4())

    # Подробное логирование для отладки
    print(f"[PDF Debug] JSON input: {json_input}")
    print(f"[PDF Debug] Template: {template_name}")
    print(f"[PDF Debug] Document ID: {document_id}")
    print(f"[PDF Debug] Current working directory: {os.getcwd()}")
    print(f"[PDF Debug] Templates directory exists: {os.path.exists('templates')}")
    print(f"[PDF Debug] Template file exists: {os.path.exists(os.path.join('templates', template_name))}")
    print(f"[PDF Debug] Template files in directory: {os.listdir('templates')}")
    print(f"[PDF Debug] wkhtmltopdf path: {wkhtmltopdf_path}")
    print(f"[PDF Debug] wkhtmltopdf exists: {os.path.exists(wkhtmltopdf_path)}")

    # Генерация QR-кода в формате base64
    qr_base64 = generate_qr_code(document_id)
    print(f"[PDF Debug] QR code generated: {len(qr_base64)} chars")
    data['qr_code'] = qr_base64

    try:
        # Проверка входных данных для шаблона
        print(f"[PDF Debug] Template data keys: {data.keys()}")
        
        # Рендеринг шаблона
        template = env.get_template(template_name)
        html_content = template.render(**data)
        
        # Проверка сгенерированного HTML
        print(f"[PDF Debug] HTML length: {len(html_content)}")
        print(f"[PDF Debug] HTML content preview: {html_content[:500]}...")
        
        # Сохраняем HTML во временный файл для отладки
        debug_html_path = f"static/debug_html_{document_id}.html"
        with open(debug_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[PDF Debug] Debug HTML saved to: {debug_html_path}")

        # Создание статического каталога, если его нет
        static_dir = os.path.join(os.getcwd(), 'static')
        os.makedirs(static_dir, exist_ok=True)
        
        # Генерация PDF в зависимости от доступного рендерера
        try:
            if pdf_renderer == "wkhtmltopdf":
                pdf_bytes, file_path = generate_pdf_with_wkhtmltopdf(html_content, document_id)
                is_html_fallback = False
            else:
                pdf_bytes, file_path = generate_pdf_fallback(html_content, document_id)
                is_html_fallback = True
        except Exception as e:
            print(f"[PDF Debug] Ошибка основного рендерера, переключение на запасной вариант: {str(e)}")
            pdf_bytes, file_path = generate_pdf_fallback(html_content, document_id)
            is_html_fallback = True
            
        # Генерируем URL для скачивания PDF
        pdf_url = url_for('static', filename=os.path.basename(file_path))
        
        # Создаем base64 версию PDF для встраивания (если это действительно PDF)
        if not is_html_fallback:
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_data_uri = f"data:application/pdf;base64,{pdf_base64}"
            print(f"[PDF Debug] PDF base64 length: {len(pdf_base64)}")
        else:
            pdf_data_uri = None
            print(f"[PDF Debug] Using HTML fallback instead of PDF base64")

        # Метаданные о документе для улучшенного отображения
        document_meta = {
            "id": document_id,
            "created_at": data.get('date', ''),
            "template_type": "акт" if template_name == "act.html" else "заявка",
            "number": data.get('document_number') or data.get('request_number', ''),
            "size_kb": round(len(pdf_bytes) / 1024, 1),
            "pages": 1,  # Примерное количество страниц
            "is_html_fallback": is_html_fallback  # Флаг, указывающий на использование HTML вместо PDF
        }
        print(f"[PDF Debug] Document meta: {document_meta}")

        # Добавляем URL к отладочному HTML в результат
        debug_html_url = url_for('static', filename=f'debug_html_{document_id}.html')
        
        return render_template('result.html', 
                               pdf_url=pdf_url,
                               pdf_data_uri=pdf_data_uri,
                               document_id=document_id, 
                               document_meta=document_meta,
                               debug_html_url=debug_html_url,
                               is_html_fallback=is_html_fallback)
                               
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[PDF Debug] ERROR: {str(e)}")
        print(f"[PDF Debug] ERROR DETAILS: {error_details}")
        return render_template('result.html', 
                               error=f"Ошибка генерации PDF: {str(e)}",
                               error_details=error_details)


@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    data = request.get_json()
    if not data:
        return {"error": "No JSON data provided"}, 400

    template_name = data.get('template', 'act.html')
    if template_name not in ['act.html', 'request.html']:
        return {"error": "Invalid template name"}, 400

    document_id = str(uuid.uuid4())

    # Логирование для отладки
    print(f"Current working directory: {os.getcwd()}")
    print(f"Trying to load template: {template_name}")
    print(f"Templates directory exists: {os.path.exists('templates')}")
    print(f"Template file exists: {os.path.exists(os.path.join('templates', template_name))}")
    print(f"wkhtmltopdf path: {wkhtmltopdf_path}")
    print(f"wkhtmltopdf exists: {os.path.exists(wkhtmltopdf_path)}")

    # Генерация QR-кода в формате base64
    qr_base64 = generate_qr_code(document_id)
    print(f"QR code base64 (first 50 chars): {qr_base64[:50]}")
    data['qr_code'] = qr_base64

    try:
        # Рендеринг шаблона
        template = env.get_template(template_name)
        html_content = template.render(**data)
        print(f"Rendered HTML (first 500 chars): {html_content[:500]}")

        # Улучшенные настройки для PDF
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

        # Генерация PDF в виде байтов
        pdf_bytes = pdfkit.from_string(html_content, False, options=pdf_options, configuration=config)

        # Запись байтов в BytesIO
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)

        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'document_{document_id}.pdf'
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}, 500


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)