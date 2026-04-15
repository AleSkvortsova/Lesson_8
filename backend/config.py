"""
Конфигурация приложения
"""
import os
import logging
import sys
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# === Настройка логирования ===
def setup_logging():
    """Настройка логирования для всего приложения"""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Основной логгер
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Уменьшаем логи от сторонних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("WDM").setLevel(logging.WARNING)
    
    return logging.getLogger("competitor_monitor")

# Инициализация логгера
logger = setup_logging()


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # ProxyAPI (OpenAI-совместимый)
    proxy_api_key: str = os.getenv("PROXY_API_KEY", "")
    proxy_api_base_url: str = "https://api.proxyapi.ru/openai/v1"
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_vision_model: str = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # История
    history_file: str = "history.json"
    max_history_items: int = 10
    competitor_collection_file: str = "competitor_collection.json"
    
    # Парсер
    parser_timeout: int = 10
    parser_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    competitor_urls: str = os.getenv("COMPETITOR_URLS", "")
    auto_collect_competitors_on_startup: bool = os.getenv("AUTO_COLLECT_COMPETITORS_ON_STARTUP", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

