import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database configuration"""
    supabase_url: str
    supabase_key: str


@dataclass
class AppConfig:
    """Application configuration"""
    secret_key: str
    debug: bool = False
    static_folder: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'static')
    templates_folder: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'templates')
    wkhtmltopdf_path: Optional[str] = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"


def load_config() -> tuple[AppConfig, DatabaseConfig]:
    """Load application configuration"""
    # Database config
    db_config = DatabaseConfig(
        supabase_url=os.environ.get('SUPABASE_URL', 'https://ddfjcrfioaymllejalpm.supabase.co'),
        supabase_key=os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRkZmpjcmZpb2F5bWxsZWphbHBtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MjQ3ODYzOSwiZXhwIjoyMDU4MDU0NjM5fQ.Dh42k1K07grKhF3DntbNLSwUifaXAa0Q6-LEIzRgpWM')
    )
    
    # App config
    app_config = AppConfig(
        secret_key=os.environ.get('SECRET_KEY', 'your_secret_key_here'),
        debug=os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
    )
    
    return app_config, db_config 