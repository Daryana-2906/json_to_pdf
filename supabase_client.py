import os
import hashlib
import uuid
import secrets
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import Dict, Optional, List, Any, Tuple
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('supabase_client')

# Конфигурация Supabase
SUPABASE_URL = "https://ddfjcrfioaymllejalpm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRkZmpjcmZpb2F5bWxsZWphbHBtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MjQ3ODYzOSwiZXhwIjoyMDU4MDU0NjM5fQ.Dh42k1K07grKhF3DntbNLSwUifaXAa0Q6-LEIzRgpWM"

class SupabaseClient:
    """Класс для работы с Supabase API"""
    
    def __init__(self):
        """Инициализирует соединение с Supabase"""
        try:
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Соединение с Supabase установлено успешно")
        except Exception as e:
            logger.error(f"Ошибка при подключении к Supabase: {str(e)}")
            raise

    def _hash_password(self, password: str) -> str:
        """
        Хеширует пароль пользователя
        
        Args:
            password: Пароль в открытом виде
            
        Returns:
            Хешированный пароль
        """
        salt = uuid.uuid4().hex
        return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

    def _verify_password(self, hashed_password: str, provided_password: str) -> bool:
        """
        Проверяет соответствие пароля хешу
        
        Args:
            hashed_password: Хешированный пароль из БД
            provided_password: Введенный пользователем пароль
            
        Returns:
            True если пароль совпадает, иначе False
        """
        password, salt = hashed_password.split(':')
        return password == hashlib.sha256(salt.encode() + provided_password.encode()).hexdigest()

    def create_user(self, email: str, name: str, password: str) -> Dict[str, Any]:
        """
        Создает нового пользователя в базе данных
        
        Args:
            email: Email пользователя
            name: Имя пользователя
            password: Пароль пользователя
            
        Returns:
            Данные созданного пользователя
        """
        try:
            # Проверяем, существует ли пользователь с таким email
            existing_user = self.get_user_by_email(email)
            if existing_user:
                logger.warning(f"Пользователь с email {email} уже существует")
                return {"error": "Пользователь с таким email уже существует"}
            
            # Хешируем пароль
            password_hash = self._hash_password(password)
            
            # Создаем пользователя
            user_data = {
                "email": email,
                "name": name,
                "password_hash": password_hash,
                "is_verified": True  # Пользователь сразу считается подтвержденным
            }
            
            result = self.supabase.table("users").insert(user_data).execute()
            
            if result.data:
                logger.info(f"Пользователь {email} успешно создан")
                return {
                    "success": True,
                    "user": result.data[0]
                }
            else:
                logger.error(f"Ошибка при создании пользователя: {result.error}")
                return {"error": "Не удалось создать пользователя"}
                
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {str(e)}")
            return {"error": f"Произошла ошибка: {str(e)}"}

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по email
        
        Args:
            email: Email пользователя
            
        Returns:
            Данные пользователя или None, если пользователь не найден
        """
        try:
            result = self.supabase.table("users").select("*").eq("email", email).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при поиске пользователя по email: {str(e)}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по ID
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Данные пользователя или None, если пользователь не найден
        """
        try:
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при поиске пользователя по ID: {str(e)}")
            return None

    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Аутентифицирует пользователя по email и паролю
        
        Args:
            email: Email пользователя
            password: Пароль пользователя
            
        Returns:
            Данные пользователя в случае успешной аутентификации
        """
        try:
            user = self.get_user_by_email(email)
            
            if not user:
                logger.warning(f"Попытка входа для несуществующего пользователя {email}")
                return {"error": "Пользователь не найден"}
                
            if not self._verify_password(user["password_hash"], password):
                logger.warning(f"Неверный пароль для пользователя {email}")
                return {"error": "Неверный пароль"}
                
            logger.info(f"Пользователь {email} успешно аутентифицирован")
            return {"success": True, "user": user}
            
        except Exception as e:
            logger.error(f"Ошибка при аутентификации пользователя: {str(e)}")
            return {"error": f"Произошла ошибка: {str(e)}"}

    def verify_user_email(self, token: str) -> Dict[str, Any]:
        """
        Подтверждает email пользователя по токену верификации
        
        Args:
            token: Токен верификации
            
        Returns:
            Результат операции
        """
        try:
            # Поиск пользователя с указанным токеном
            result = self.supabase.table("users") \
                .select("*") \
                .eq("verification_token", token) \
                .execute()
                
            if not result.data or len(result.data) == 0:
                logger.warning(f"Попытка верификации с недействительным токеном: {token}")
                return {"error": "Недействительный токен верификации"}
                
            user = result.data[0]
            
            # Проверка срока действия токена
            expiration_time = datetime.fromisoformat(user["verification_token_expires_at"])
            if datetime.now() > expiration_time:
                logger.warning(f"Попытка верификации с истекшим токеном: {token}")
                return {"error": "Срок действия токена истек"}
                
            # Обновление статуса верификации
            update_data = {
                "is_verified": True,
                "verification_token": None,
                "verification_token_expires_at": None
            }
            
            self.supabase.table("users") \
                .update(update_data) \
                .eq("id", user["id"]) \
                .execute()
                
            logger.info(f"Пользователь {user['email']} успешно верифицирован")
            return {"success": True, "user": user}
            
        except Exception as e:
            logger.error(f"Ошибка при верификации пользователя: {str(e)}")
            return {"error": f"Произошла ошибка: {str(e)}"}

    def save_document(self, user_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сохраняет информацию о документе в базу данных
        
        Args:
            user_id: ID пользователя
            document_data: Данные документа (имя, тип, путь к файлу и т.д.)
            
        Returns:
            Результат операции
        """
        try:
            # Проверяем существование пользователя
            user = self.get_user_by_id(user_id)
            if not user:
                logger.warning(f"Попытка сохранить документ для несуществующего пользователя {user_id}")
                return {"error": "Пользователь не найден"}
                
            # Формируем данные документа для сохранения
            save_data = {
                "user_id": user_id,
                "document_name": document_data.get("document_name", "Без названия"),
                "document_number": document_data.get("document_number"),
                "operation_type": document_data.get("operation_type", "Другое"),
                "file_path": document_data.get("file_path"),
                "file_size_kb": document_data.get("file_size_kb"),
                "pages": document_data.get("pages", 1),
                "json_data": document_data.get("json_data")
            }
            
            # Проверка обязательных полей
            if not save_data["file_path"]:
                return {"error": "Путь к файлу не указан"}
                
            result = self.supabase.table("documents").insert(save_data).execute()
            
            if result.data:
                logger.info(f"Документ {save_data['document_name']} успешно сохранен для пользователя {user_id}")
                return {"success": True, "document": result.data[0]}
            else:
                logger.error(f"Ошибка при сохранении документа: {result.error}")
                return {"error": "Не удалось сохранить документ"}
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении документа: {str(e)}")
            return {"error": f"Произошла ошибка: {str(e)}"}

    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Получает список документов пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список документов пользователя
        """
        try:
            result = self.supabase.table("documents") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .execute()
                
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Ошибка при получении документов пользователя: {str(e)}")
            return []

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о документе по его ID
        
        Args:
            document_id: ID документа
            
        Returns:
            Данные документа или None, если документ не найден
        """
        try:
            result = self.supabase.table("documents") \
                .select("*") \
                .eq("id", document_id) \
                .execute()
                
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении документа по ID: {str(e)}")
            return None

    def update_user_profile(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обновляет профиль пользователя
        
        Args:
            user_id: ID пользователя
            update_data: Данные для обновления
            
        Returns:
            Результат операции
        """
        try:
            # Проверяем существование пользователя
            user = self.get_user_by_id(user_id)
            if not user:
                logger.warning(f"Попытка обновить несуществующего пользователя {user_id}")
                return {"error": "Пользователь не найден"}
                
            # Формируем данные для обновления
            safe_update_data = {k: v for k, v in update_data.items() if k in ["name", "avatar_url"]}
            
            if not safe_update_data:
                return {"error": "Нет данных для обновления"}
                
            result = self.supabase.table("users") \
                .update(safe_update_data) \
                .eq("id", user_id) \
                .execute()
                
            if result.data:
                logger.info(f"Профиль пользователя {user_id} успешно обновлен")
                return {"success": True, "user": result.data[0]}
            else:
                logger.error(f"Ошибка при обновлении профиля: {result.error}")
                return {"error": "Не удалось обновить профиль"}
                
        except Exception as e:
            logger.error(f"Ошибка при обновлении профиля пользователя: {str(e)}")
            return {"error": f"Произошла ошибка: {str(e)}"}

    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Создает запрос на сброс пароля
        
        Args:
            email: Email пользователя
            
        Returns:
            Результат операции с токеном сброса
        """
        try:
            user = self.get_user_by_email(email)
            if not user:
                # Не сообщаем о несуществующем пользователе для безопасности
                logger.info(f"Запрос на сброс пароля для несуществующего пользователя {email}")
                return {"success": True, "message": "Если учетная запись существует, инструкции были отправлены на указанный email"}
                
            # Генерируем токен для сброса пароля
            reset_token = secrets.token_urlsafe(32)
            expiration_time = datetime.now() + timedelta(hours=24)
            
            # Сохраняем токен в базе данных
            token_data = {
                "user_id": user["id"],
                "token": reset_token,
                "expires_at": expiration_time.isoformat()
            }
            
            self.supabase.table("password_reset_tokens").insert(token_data).execute()
            
            logger.info(f"Создан токен сброса пароля для пользователя {email}")
            return {
                "success": True,
                "message": "Инструкции по сбросу пароля отправлены на ваш email",
                "reset_token": reset_token,  # В реальном приложении токен отправляется по email
                "user_id": user["id"]
            }
            
        except Exception as e:
            logger.error(f"Ошибка при создании запроса на сброс пароля: {str(e)}")
            return {"error": f"Произошла ошибка: {str(e)}"}

    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """
        Сбрасывает пароль пользователя
        
        Args:
            token: Токен сброса пароля
            new_password: Новый пароль
            
        Returns:
            Результат операции
        """
        try:
            # Поиск токена в базе
            result = self.supabase.table("password_reset_tokens") \
                .select("*,users!inner(*)") \
                .eq("token", token) \
                .execute()
                
            if not result.data or len(result.data) == 0:
                logger.warning(f"Попытка сброса пароля с недействительным токеном: {token}")
                return {"error": "Недействительный токен сброса пароля"}
                
            token_data = result.data[0]
            user_id = token_data["user_id"]
            
            # Проверка срока действия токена
            expiration_time = datetime.fromisoformat(token_data["expires_at"])
            if datetime.now() > expiration_time:
                logger.warning(f"Попытка сброса пароля с истекшим токеном: {token}")
                return {"error": "Срок действия токена истек"}
                
            # Хешируем новый пароль
            password_hash = self._hash_password(new_password)
            
            # Обновляем пароль пользователя
            self.supabase.table("users") \
                .update({"password_hash": password_hash}) \
                .eq("id", user_id) \
                .execute()
                
            # Удаляем использованный токен
            self.supabase.table("password_reset_tokens") \
                .delete() \
                .eq("token", token) \
                .execute()
                
            logger.info(f"Пароль успешно сброшен для пользователя {user_id}")
            return {"success": True, "message": "Пароль успешно обновлен"}
            
        except Exception as e:
            logger.error(f"Ошибка при сбросе пароля: {str(e)}")
            return {"error": f"Произошла ошибка: {str(e)}"}

# Создаем экземпляр клиента для использования в приложении
supabase_client = SupabaseClient() 