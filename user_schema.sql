-- Создаем таблицу пользователей
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_verified BOOLEAN DEFAULT TRUE
);

-- Создаем индексы для более быстрого поиска
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Функция для автоматического обновления поля updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для обновления timestamp в таблице пользователей
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Добавляем Row Level Security (RLS) для безопасности
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Политики доступа: пользователь может видеть и изменять только свои данные
CREATE POLICY user_crud_policy ON users
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid()); 