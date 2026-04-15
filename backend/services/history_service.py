"""
Сервис для работы с историей запросов
"""
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from backend.config import settings
from backend.models.schemas import HistoryItem

# Логгер для сервиса
logger = logging.getLogger("competitor_monitor.history")


class HistoryService:
    """Управление историей запросов"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("Инициализация History сервиса")
        
        self.history_file = Path(settings.history_file)
        self.max_items = settings.max_history_items
        
        logger.info(f"  Файл истории: {self.history_file}")
        logger.info(f"  Макс. записей: {self.max_items}")
        
        self._ensure_file_exists()
        
        # Загружаем и показываем текущее состояние
        history = self._load_history()
        logger.info(f"  Текущих записей: {len(history)}")
        logger.info("History сервис инициализирован ✓")
        logger.info("=" * 50)
    
    def _ensure_file_exists(self):
        """Создать файл истории если его нет"""
        if not self.history_file.exists():
            logger.info(f"  📁 Создание файла истории: {self.history_file}")
            self.history_file.write_text("[]", encoding="utf-8")
            logger.info("  ✓ Файл создан")
        else:
            logger.debug(f"  Файл истории существует: {self.history_file}")
    
    def _load_history(self) -> List[dict]:
        """Загрузить историю из файла"""
        try:
            content = self.history_file.read_text(encoding="utf-8")
            history = json.loads(content)
            logger.debug(f"История загружена: {len(history)} записей")
            return history
        except json.JSONDecodeError as e:
            logger.warning(f"Ошибка парсинга JSON истории: {e}")
            return []
        except FileNotFoundError:
            logger.warning(f"Файл истории не найден: {self.history_file}")
            return []
    
    def _save_history(self, history: List[dict]):
        """Сохранить историю в файл"""
        logger.debug(f"Сохранение истории: {len(history)} записей")
        self.history_file.write_text(
            json.dumps(history, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )
        logger.debug("История сохранена ✓")
    
    def add_entry(
        self,
        request_type: str,
        request_summary: str,
        response_summary: str
    ) -> HistoryItem:
        """Добавить запись в историю"""
        logger.info(f"📝 Добавление записи в историю")
        logger.info(f"  Тип: {request_type}")
        logger.info(f"  Запрос: {request_summary[:50]}...")
        logger.info(f"  Ответ: {response_summary[:50]}...")
        
        history = self._load_history()
        
        item = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "request_type": request_type,
            "request_summary": request_summary[:200],
            "response_summary": response_summary[:500]
        }
        
        # Добавляем в начало
        history.insert(0, item)
        old_count = len(history)
        
        # Оставляем только последние N записей
        history = history[:self.max_items]
        
        if old_count > len(history):
            logger.info(f"  🗑️ Удалено старых записей: {old_count - len(history)}")
        
        self._save_history(history)
        
        logger.info(f"  ✓ Запись добавлена (ID: {item['id'][:8]}...)")
        logger.info(f"  Всего записей: {len(history)}")
        
        return HistoryItem(**item)
    
    def get_history(self) -> List[HistoryItem]:
        """Получить всю историю"""
        logger.info("📋 Получение истории")
        history = self._load_history()
        logger.info(f"  Записей: {len(history)}")
        return [HistoryItem(**item) for item in history]
    
    def clear_history(self):
        """Очистить историю"""
        logger.info("🗑️ Очистка истории")
        old_history = self._load_history()
        logger.info(f"  Удаляется записей: {len(old_history)}")
        
        self._save_history([])
        
        logger.info("  ✓ История очищена")


# Глобальный экземпляр
logger.info("Создание глобального экземпляра History сервиса...")
history_service = HistoryService()
