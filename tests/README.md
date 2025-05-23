# Модульные тесты для проекта JSON to PDF

Данный каталог содержит модульные тесты для ключевых компонентов приложения JSON to PDF.

## Структура тестов

- **test_user_service.py** - тесты для сервиса управления пользователями
- **test_document_service.py** - тесты для сервиса управления документами
- **test_pdf_generator.py** - тесты для адаптера генерации PDF-документов
- **test_qr_generator.py** - тесты для адаптера генерации QR-кодов
- **test_supabase_repository.py** - тесты для репозитория данных на базе Supabase

## Запуск тестов

Для запуска всех тестов используйте следующую команду:

```bash
python -m unittest discover tests
```

Для запуска отдельного тестового файла:

```bash
python -m unittest tests/test_user_service.py
```

## Описание тестов

### UserService (test_user_service.py)

Тесты проверяют корректность работы сервиса пользователей:
- Создание нового пользователя
- Проверка ошибки при попытке создать пользователя с уже существующим email
- Аутентификация пользователя с корректными и некорректными данными
- Получение пользователя по ID и email

### DocumentService (test_document_service.py)

Тесты проверяют корректность работы сервиса документов:
- Сохранение документа
- Получение списка документов пользователя
- Получение документа по ID
- Генерация PDF из HTML-контента
- Генерация QR-кода для документа
- Создание документа из HTML-контента с встроенным QR-кодом

### PDFGeneratorAdapter (test_pdf_generator.py)

Тесты проверяют работу адаптера генерации PDF-документов:
- Инициализация адаптера с наличием и отсутствием wkhtmltopdf
- Генерация PDF с использованием wkhtmltopdf
- Резервный метод генерации документа (fallback) при отсутствии wkhtmltopdf

### QRCodeGeneratorAdapter (test_qr_generator.py)

Тесты проверяют работу адаптера генерации QR-кодов:
- Инициализация генератора QR-кодов
- Генерация QR-кода с корректным URL верификации
- Интеграционный тест генерации QR-кода
- Проверка использования разных базовых URL для верификации

### SupabaseRepository (test_supabase_repository.py)

Тесты проверяют работу репозитория данных на базе Supabase:
- Создание пользователя (успешный случай и случай с существующим email)
- Получение пользователя по email (существующий и несуществующий)
- Аутентификация пользователя (успешная и с неверным паролем)
- Сохранение документа
- Получение всех документов пользователя

## Покрытие тестами

Тесты покрывают основную функциональность приложения, включая:

1. **Бизнес-логику** (сервисы):
   - Управление пользователями
   - Управление документами

2. **Инфраструктуру** (адаптеры):
   - Хранение данных (Supabase)
   - Генерация PDF-документов
   - Генерация QR-кодов

Для всех тестов используются моки (mock objects) для изоляции тестируемого компонента от его зависимостей. 