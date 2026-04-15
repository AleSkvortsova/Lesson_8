# Создание мультимодального ассистента мониторинга конкурентов
_Exported on 12/7/2025 at 05:37:56 GMT+3 from Cursor (2.1.42)_

---

**User**

Создай полнофункциональное мультимодальное приложение с поддержкой текста и изображений.



Проект должен быть реализован на Python.

Требования к проекту:

1. Общая архитектура

Проект состоит из:

Python backend (FastAPI).

Клиентского интерфейса — на выбор:

мини-веб-приложение (HTML + JS),



Приложение — MVP ассистента “Мониторинг конкурентов”.

Поддержка мультимодальности: пользователь может отправлять текст и изображения.

2. Функциональность ассистента

Реализовать такие функции:

Анализ конкурентного текста

Пользователь отправляет текст → модель даёт структурированную аналитику:

сильные стороны конкурента

слабые стороны

уникальные предложения

рекомендации по улучшению стратегии

Анализ изображений

Пользователь отправляет фото баннера, сайта, упаковки товара →

модель возвращает:

описание изображения

маркетинговые инсайты

оценку визуального стиля конкурента

Сбор данных из внешних источников (демо)

Создать отдельный endpoint /parse_demo, который принимает URL,

делает HTTP-запрос, извлекает title + h1 + первый абзац,

и передаёт их модели для анализа.

История запросов (простая)

Хранить последние 10 запросов пользователя в файле history.json.

3. Backend (FastAPI)

Сделай:

эндпоинт /analyze_text

эндпоинт /analyze_image

эндпоинт /parse_demo

эндпоинт /history

конфиг для OpenAI (модель GPT-4.1 / GPT-4o-mini)

Все ответы возвращать в JSON.

4. Telegram-бот (вариант исполнения)

Если выбираешь Telegram-бот:

Бот должен уметь:

принимать текст → отправлять его в /analyze_text

принимать изображения → передавать их в /analyze_image

команду /parse <url> → парсить сайт через /parse_demo

команду /history → показывать историю взаимодействий

использовать удобное меню команд

5. UI-вариант (если вместо бота)

Мини-страница:

Поле ввода текста

Поле загрузки изображения

Кнопка «Проанализировать»

Блок результатов

Простая верстка (без лагерей, но современно).

6. Качество кода

Исправлять ошибки автоматически

Разбивать на модули

Добавить README:

описание проекта

как запускать

какие функции реализованы

7. Документация

Создай docs.md, где будет:

структура проекта

описание API

примеры запросов

описание мультимодальных функций

---

**Cursor**

Создам полнофункциональное мультимодальное приложение для мониторинга конкурентов. Начну с создания структуры проекта.

```pip-requirements
fastapi==0.104.1
uvicorn==0.24.0
openai==1.6.1
httpx==0.25.2
python-multipart==0.0.6
beautifulsoup4==4.12.2
lxml==4.9.4
pydantic==2.5.2
pydantic-settings==2.1.0
python-dotenv==1.0.0
aiofiles==23.2.1
Pillow==10.1.0

```

```python
"""
Конфигурация приложения
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_vision_model: str = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # История
    history_file: str = "history.json"
    max_history_items: int = 10
    
    # Парсер
    parser_timeout: int = 10
    parser_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

```

```python
"""
Pydantic схемы для API
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# === Запросы ===

class TextAnalysisRequest(BaseModel):
    """Запрос на анализ текста"""
    text: str = Field(..., min_length=10, description="Текст для анализа")


class ParseDemoRequest(BaseModel):
    """Запрос на парсинг URL"""
    url: str = Field(..., description="URL для парсинга")


# === Ответы ===

class CompetitorAnalysis(BaseModel):
    """Структурированный анализ конкурента"""
    strengths: List[str] = Field(default_factory=list, description="Сильные стороны")
    weaknesses: List[str] = Field(default_factory=list, description="Слабые стороны")
    unique_offers: List[str] = Field(default_factory=list, description="Уникальные предложения")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")
    summary: str = Field("", description="Общее резюме")


class ImageAnalysis(BaseModel):
    """Анализ изображения"""
    description: str = Field("", description="Описание изображения")
    marketing_insights: List[str] = Field(default_factory=list, description="Маркетинговые инсайты")
    visual_style_score: int = Field(0, ge=0, le=10, description="Оценка визуального стиля (0-10)")
    visual_style_analysis: str = Field("", description="Анализ визуального стиля")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")


class ParsedContent(BaseModel):
    """Результат парсинга страницы"""
    url: str
    title: Optional[str] = None
    h1: Optional[str] = None
    first_paragraph: Optional[str] = None
    analysis: Optional[CompetitorAnalysis] = None
    error: Optional[str] = None


class TextAnalysisResponse(BaseModel):
    """Ответ на анализ текста"""
    success: bool
    analysis: Optional[CompetitorAnalysis] = None
    error: Optional[str] = None


class ImageAnalysisResponse(BaseModel):
    """Ответ на анализ изображения"""
    success: bool
    analysis: Optional[ImageAnalysis] = None
    error: Optional[str] = None


class ParseDemoResponse(BaseModel):
    """Ответ на парсинг"""
    success: bool
    data: Optional[ParsedContent] = None
    error: Optional[str] = None


# === История ===

class HistoryItem(BaseModel):
    """Элемент истории"""
    id: str
    timestamp: datetime
    request_type: str  # "text", "image", "parse"
    request_summary: str
    response_summary: str


class HistoryResponse(BaseModel):
    """Ответ со списком истории"""
    items: List[HistoryItem]
    total: int

```

```python
from .schemas import *

```

```python
from .openai_service import OpenAIService
from .parser_service import ParserService
from .history_service import HistoryService

```

```python
"""
Сервис для работы с историей запросов
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from backend.config import settings
from backend.models.schemas import HistoryItem


class HistoryService:
    """Управление историей запросов"""
    
    def __init__(self):
        self.history_file = Path(settings.history_file)
        self.max_items = settings.max_history_items
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Создать файл истории если его нет"""
        if not self.history_file.exists():
            self.history_file.write_text("[]", encoding="utf-8")
    
    def _load_history(self) -> List[dict]:
        """Загрузить историю из файла"""
        try:
            content = self.history_file.read_text(encoding="utf-8")
            return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_history(self, history: List[dict]):
        """Сохранить историю в файл"""
        self.history_file.write_text(
            json.dumps(history, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )
    
    def add_entry(
        self,
        request_type: str,
        request_summary: str,
        response_summary: str
    ) -> HistoryItem:
        """Добавить запись в историю"""
        history = self._load_history()
        
        item = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "request_type": request_type,
            "request_summary": request_summary[:200],  # Ограничиваем длину
            "response_summary": response_summary[:500]
        }
        
        # Добавляем в начало
        history.insert(0, item)
        
        # Оставляем только последние N записей
        history = history[:self.max_items]
        
        self._save_history(history)
        
        return HistoryItem(**item)
    
    def get_history(self) -> List[HistoryItem]:
        """Получить всю историю"""
        history = self._load_history()
        return [HistoryItem(**item) for item in history]
    
    def clear_history(self):
        """Очистить историю"""
        self._save_history([])


# Глобальный экземпляр
history_service = HistoryService()

```

```python
"""
Сервис для работы с OpenAI API
"""
import base64
import json
import re
from typing import Optional

from openai import OpenAI

from backend.config import settings
from backend.models.schemas import CompetitorAnalysis, ImageAnalysis


class OpenAIService:
    """Сервис для анализа через OpenAI"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.vision_model = settings.openai_vision_model
    
    def _parse_json_response(self, content: str) -> dict:
        """Извлечь JSON из ответа модели"""
        # Пробуем найти JSON в markdown блоке
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)
        
        # Пробуем найти JSON объект
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}
    
    async def analyze_text(self, text: str) -> CompetitorAnalysis:
        """Анализ текста конкурента"""
        system_prompt = """Ты — эксперт по конкурентному анализу. Проанализируй предоставленный текст конкурента и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
    "weaknesses": ["слабая сторона 1", "слабая сторона 2", ...],
    "unique_offers": ["уникальное предложение 1", "уникальное предложение 2", ...],
    "recommendations": ["рекомендация 1", "рекомендация 2", ...],
    "summary": "Краткое резюме анализа"
}

Важно:
- Каждый массив должен содержать 3-5 пунктов
- Пиши на русском языке
- Будь конкретен и практичен в рекомендациях"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Проанализируй текст конкурента:\n\n{text}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        data = self._parse_json_response(content)
        
        return CompetitorAnalysis(
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            unique_offers=data.get("unique_offers", []),
            recommendations=data.get("recommendations", []),
            summary=data.get("summary", "")
        )
    
    async def analyze_image(self, image_base64: str, mime_type: str = "image/jpeg") -> ImageAnalysis:
        """Анализ изображения (баннер, сайт, упаковка)"""
        system_prompt = """Ты — эксперт по визуальному маркетингу и дизайну. Проанализируй изображение конкурента (баннер, сайт, упаковка товара и т.д.) и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "description": "Детальное описание того, что изображено",
    "marketing_insights": ["инсайт 1", "инсайт 2", ...],
    "visual_style_score": 7,
    "visual_style_analysis": "Анализ визуального стиля конкурента",
    "recommendations": ["рекомендация 1", "рекомендация 2", ...]
}

Важно:
- visual_style_score от 0 до 10
- Каждый массив должен содержать 3-5 пунктов
- Пиши на русском языке
- Оценивай: цветовую палитру, типографику, композицию, UX/UI элементы"""

        response = self.client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Проанализируй это изображение конкурента с точки зрения маркетинга и дизайна:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        data = self._parse_json_response(content)
        
        return ImageAnalysis(
            description=data.get("description", ""),
            marketing_insights=data.get("marketing_insights", []),
            visual_style_score=data.get("visual_style_score", 5),
            visual_style_analysis=data.get("visual_style_analysis", ""),
            recommendations=data.get("recommendations", [])
        )
    
    async def analyze_parsed_content(
        self, 
        title: Optional[str], 
        h1: Optional[str], 
        paragraph: Optional[str]
    ) -> CompetitorAnalysis:
        """Анализ распарсенного контента сайта"""
        content_parts = []
        if title:
            content_parts.append(f"Заголовок страницы (title): {title}")
        if h1:
            content_parts.append(f"Главный заголовок (H1): {h1}")
        if paragraph:
            content_parts.append(f"Первый абзац: {paragraph}")
        
        combined_text = "\n\n".join(content_parts)
        
        if not combined_text.strip():
            return CompetitorAnalysis(
                summary="Не удалось извлечь контент для анализа"
            )
        
        return await self.analyze_text(combined_text)


# Глобальный экземпляр
openai_service = OpenAIService()

```

```python
"""
Сервис для парсинга веб-страниц
"""
from typing import Optional, Tuple
import httpx
from bs4 import BeautifulSoup

from backend.config import settings


class ParserService:
    """Парсинг веб-страниц"""
    
    def __init__(self):
        self.timeout = settings.parser_timeout
        self.user_agent = settings.parser_user_agent
    
    async def parse_url(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Парсит URL и извлекает title, h1, первый абзац
        
        Returns:
            Tuple[title, h1, first_paragraph, error]
        """
        # Добавляем протокол если его нет
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": self.user_agent}
                )
                response.raise_for_status()
                
                html = response.text
                soup = BeautifulSoup(html, 'lxml')
                
                # Извлекаем title
                title = None
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                
                # Извлекаем h1
                h1 = None
                h1_tag = soup.find('h1')
                if h1_tag:
                    h1 = h1_tag.get_text(strip=True)
                
                # Извлекаем первый абзац
                first_paragraph = None
                
                # Пробуем найти абзац в основном контенте
                main_content = soup.find(['main', 'article']) or soup.find('body')
                if main_content:
                    # Ищем первый непустой абзац
                    for p in main_content.find_all('p'):
                        text = p.get_text(strip=True)
                        if len(text) > 50:  # Минимальная длина для значимого абзаца
                            first_paragraph = text[:500]  # Ограничиваем длину
                            break
                
                return title, h1, first_paragraph, None
                
        except httpx.TimeoutException:
            return None, None, None, "Превышено время ожидания запроса"
        except httpx.HTTPStatusError as e:
            return None, None, None, f"HTTP ошибка: {e.response.status_code}"
        except httpx.RequestError as e:
            return None, None, None, f"Ошибка запроса: {str(e)}"
        except Exception as e:
            return None, None, None, f"Неизвестная ошибка: {str(e)}"


# Глобальный экземпляр
parser_service = ParserService()

```

```python
# Backend package

```

```python
"""
Главный модуль FastAPI приложения
Мониторинг конкурентов - MVP ассистент
"""
import base64
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from backend.config import settings
from backend.models.schemas import (
    TextAnalysisRequest,
    TextAnalysisResponse,
    ImageAnalysisResponse,
    ParseDemoRequest,
    ParseDemoResponse,
    ParsedContent,
    HistoryResponse
)
from backend.services.openai_service import openai_service
from backend.services.parser_service import parser_service
from backend.services.history_service import history_service


# Инициализация приложения
app = FastAPI(
    title="Мониторинг конкурентов",
    description="MVP ассистент для анализа конкурентов с поддержкой текста и изображений",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Эндпоинты ===

@app.get("/")
async def root():
    """Главная страница - отдаём фронтенд"""
    return FileResponse("frontend/index.html")


@app.post("/analyze_text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Анализ текста конкурента
    
    Принимает текст и возвращает структурированную аналитику:
    - Сильные стороны
    - Слабые стороны
    - Уникальные предложения
    - Рекомендации по улучшению стратегии
    """
    try:
        analysis = await openai_service.analyze_text(request.text)
        
        # Сохраняем в историю
        history_service.add_entry(
            request_type="text",
            request_summary=request.text[:100] + "..." if len(request.text) > 100 else request.text,
            response_summary=analysis.summary
        )
        
        return TextAnalysisResponse(
            success=True,
            analysis=analysis
        )
    except Exception as e:
        return TextAnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/analyze_image", response_model=ImageAnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    Анализ изображения конкурента
    
    Принимает изображение (баннер, сайт, упаковка) и возвращает:
    - Описание изображения
    - Маркетинговые инсайты
    - Оценку визуального стиля
    - Рекомендации
    """
    # Проверяем тип файла
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(allowed_types)}"
        )
    
    try:
        # Читаем и кодируем изображение
        content = await file.read()
        image_base64 = base64.b64encode(content).decode('utf-8')
        
        # Анализируем
        analysis = await openai_service.analyze_image(
            image_base64=image_base64,
            mime_type=file.content_type
        )
        
        # Сохраняем в историю
        history_service.add_entry(
            request_type="image",
            request_summary=f"Изображение: {file.filename}",
            response_summary=analysis.description[:200] if analysis.description else "Анализ изображения"
        )
        
        return ImageAnalysisResponse(
            success=True,
            analysis=analysis
        )
    except Exception as e:
        return ImageAnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/parse_demo", response_model=ParseDemoResponse)
async def parse_demo(request: ParseDemoRequest):
    """
    Парсинг и анализ сайта конкурента (демо)
    
    Принимает URL, извлекает:
    - Title страницы
    - H1 заголовок
    - Первый абзац
    
    И передаёт их модели для анализа
    """
    try:
        # Парсим страницу
        title, h1, first_paragraph, error = await parser_service.parse_url(request.url)
        
        if error:
            return ParseDemoResponse(
                success=False,
                error=error
            )
        
        # Анализируем извлечённый контент
        analysis = await openai_service.analyze_parsed_content(
            title=title,
            h1=h1,
            paragraph=first_paragraph
        )
        
        parsed_content = ParsedContent(
            url=request.url,
            title=title,
            h1=h1,
            first_paragraph=first_paragraph,
            analysis=analysis
        )
        
        # Сохраняем в историю
        history_service.add_entry(
            request_type="parse",
            request_summary=f"URL: {request.url}",
            response_summary=f"Title: {title or 'N/A'}"
        )
        
        return ParseDemoResponse(
            success=True,
            data=parsed_content
        )
    except Exception as e:
        return ParseDemoResponse(
            success=False,
            error=str(e)
        )


@app.get("/history", response_model=HistoryResponse)
async def get_history():
    """
    Получить историю последних 10 запросов
    """
    items = history_service.get_history()
    return HistoryResponse(
        items=items,
        total=len(items)
    )


@app.delete("/history")
async def clear_history():
    """
    Очистить историю запросов
    """
    history_service.clear_history()
    return {"success": True, "message": "История очищена"}


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {
        "status": "healthy",
        "service": "Competitor Monitor",
        "version": "1.0.0"
    }


# Статические файлы для фронтенда
app.mount("/static", StaticFiles(directory="frontend"), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

```

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Мониторинг конкурентов | AI Ассистент</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="app">
        <!-- Sidebar -->
        <aside class="sidebar">
            <div class="logo">
                <div class="logo-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                </div>
                <span>CompetitorAI</span>
            </div>
            
            <nav class="nav">
                <button class="nav-btn active" data-tab="text">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                        <line x1="16" y1="13" x2="8" y2="13"/>
                        <line x1="16" y1="17" x2="8" y2="17"/>
                    </svg>
                    Анализ текста
                </button>
                <button class="nav-btn" data-tab="image">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5"/>
                        <polyline points="21 15 16 10 5 21"/>
                    </svg>
                    Анализ изображений
                </button>
                <button class="nav-btn" data-tab="parse">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="2" y1="12" x2="22" y2="12"/>
                        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                    </svg>
                    Парсинг сайта
                </button>
                <button class="nav-btn" data-tab="history">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    История
                </button>
            </nav>
            
            <div class="sidebar-footer">
                <div class="status-indicator">
                    <span class="status-dot"></span>
                    <span>Система активна</span>
                </div>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="main">
            <header class="header">
                <h1 class="page-title">Мониторинг конкурентов</h1>
                <p class="page-subtitle">AI-ассистент для анализа конкурентной среды</p>
            </header>

            <div class="content">
                <!-- Text Analysis Tab -->
                <section class="tab-content active" id="text-tab">
                    <div class="card">
                        <div class="card-header">
                            <h2>Анализ текста конкурента</h2>
                            <p>Вставьте текст с сайта конкурента, из рекламы или описания продукта</p>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                <label for="competitor-text">Текст для анализа</label>
                                <textarea 
                                    id="competitor-text" 
                                    placeholder="Вставьте текст конкурента для анализа...&#10;&#10;Например: описание продукта, текст с лендинга, рекламное объявление..."
                                    rows="8"
                                ></textarea>
                            </div>
                            <button class="btn btn-primary" id="analyze-text-btn">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                                </svg>
                                Проанализировать
                            </button>
                        </div>
                    </div>
                </section>

                <!-- Image Analysis Tab -->
                <section class="tab-content" id="image-tab">
                    <div class="card">
                        <div class="card-header">
                            <h2>Анализ изображений</h2>
                            <p>Загрузите скриншот сайта, баннер или фото упаковки конкурента</p>
                        </div>
                        <div class="card-body">
                            <div class="upload-zone" id="upload-zone">
                                <input type="file" id="image-input" accept="image/*" hidden>
                                <div class="upload-content">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                        <polyline points="17 8 12 3 7 8"/>
                                        <line x1="12" y1="3" x2="12" y2="15"/>
                                    </svg>
                                    <p>Перетащите изображение или <span>выберите файл</span></p>
                                    <small>PNG, JPG, GIF, WEBP до 10MB</small>
                                </div>
                                <div class="preview-container" id="preview-container" hidden>
                                    <img id="image-preview" alt="Preview">
                                    <button class="remove-btn" id="remove-image">×</button>
                                </div>
                            </div>
                            <button class="btn btn-primary" id="analyze-image-btn" disabled>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                                </svg>
                                Проанализировать
                            </button>
                        </div>
                    </div>
                </section>

                <!-- Parse Demo Tab -->
                <section class="tab-content" id="parse-tab">
                    <div class="card">
                        <div class="card-header">
                            <h2>Парсинг сайта конкурента</h2>
                            <p>Введите URL сайта для автоматического извлечения и анализа контента</p>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                <label for="url-input">URL сайта</label>
                                <div class="input-group">
                                    <span class="input-prefix">https://</span>
                                    <input 
                                        type="text" 
                                        id="url-input" 
                                        placeholder="example.com"
                                    >
                                </div>
                            </div>
                            <button class="btn btn-primary" id="parse-btn">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                                </svg>
                                Парсить и анализировать
                            </button>
                        </div>
                    </div>
                </section>

                <!-- History Tab -->
                <section class="tab-content" id="history-tab">
                    <div class="card">
                        <div class="card-header">
                            <div class="header-with-action">
                                <div>
                                    <h2>История запросов</h2>
                                    <p>Последние 10 запросов к системе</p>
                                </div>
                                <button class="btn btn-secondary" id="clear-history-btn">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="3 6 5 6 21 6"/>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                    </svg>
                                    Очистить
                                </button>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="history-list" id="history-list">
                                <div class="history-empty">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="12" cy="12" r="10"/>
                                        <polyline points="12 6 12 12 16 14"/>
                                    </svg>
                                    <p>История пуста</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Results Section -->
                <section class="results-section" id="results-section" hidden>
                    <div class="card results-card">
                        <div class="card-header">
                            <div class="header-with-action">
                                <h2>Результаты анализа</h2>
                                <button class="btn btn-icon" id="close-results">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <line x1="18" y1="6" x2="6" y2="18"/>
                                        <line x1="6" y1="6" x2="18" y2="18"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                        <div class="card-body">
                            <div id="results-content"></div>
                        </div>
                    </div>
                </section>
            </div>
        </main>
    </div>

    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loading-overlay" hidden>
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Анализирую данные...</p>
        </div>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>

```

```css
/* === Variables === */
:root {
    /* Colors - Dark theme with cyan accents */
    --bg-primary: #0a0f1c;
    --bg-secondary: #111827;
    --bg-card: #1a2234;
    --bg-hover: #243049;
    --bg-input: #0d1320;
    
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    
    --accent-primary: #06b6d4;
    --accent-secondary: #22d3ee;
    --accent-glow: rgba(6, 182, 212, 0.3);
    
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    
    --border-color: #1e293b;
    --border-light: #334155;
    
    /* Typography */
    --font-primary: 'Outfit', -apple-system, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    
    /* Spacing */
    --sidebar-width: 280px;
    --header-height: 80px;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    
    /* Transitions */
    --transition-fast: 150ms ease;
    --transition-normal: 250ms ease;
}

/* === Reset & Base === */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    font-size: 16px;
    scroll-behavior: smooth;
}

body {
    font-family: var(--font-primary);
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
    overflow-x: hidden;
}

/* Background pattern */
body::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(6, 182, 212, 0.15), transparent),
        radial-gradient(ellipse 60% 40% at 100% 100%, rgba(139, 92, 246, 0.1), transparent);
    pointer-events: none;
    z-index: -1;
}

/* === App Layout === */
.app {
    display: flex;
    min-height: 100vh;
}

/* === Sidebar === */
.sidebar {
    width: var(--sidebar-width);
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    position: fixed;
    height: 100vh;
    z-index: 100;
}

.logo {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 24px;
    border-bottom: 1px solid var(--border-color);
}

.logo-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 15px var(--accent-glow);
}

.logo-icon svg {
    width: 24px;
    height: 24px;
    color: white;
}

.logo span {
    font-size: 1.25rem;
    font-weight: 600;
    background: linear-gradient(135deg, var(--text-primary), var(--accent-secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.nav {
    flex: 1;
    padding: 16px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.nav-btn {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    padding: 14px 16px;
    background: transparent;
    border: none;
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    font-family: inherit;
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    transition: var(--transition-normal);
    text-align: left;
}

.nav-btn svg {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
}

.nav-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
}

.nav-btn.active {
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(6, 182, 212, 0.1));
    color: var(--accent-secondary);
    box-shadow: inset 0 0 0 1px rgba(6, 182, 212, 0.3);
}

.sidebar-footer {
    padding: 16px 24px;
    border-top: 1px solid var(--border-color);
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: var(--text-muted);
}

.status-dot {
    width: 8px;
    height: 8px;
    background: var(--success);
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* === Main Content === */
.main {
    flex: 1;
    margin-left: var(--sidebar-width);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.header {
    padding: 32px 40px;
    border-bottom: 1px solid var(--border-color);
    background: rgba(17, 24, 39, 0.5);
    backdrop-filter: blur(10px);
}

.page-title {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 8px;
    background: linear-gradient(135deg, var(--text-primary), var(--accent-secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.page-subtitle {
    color: var(--text-secondary);
    font-size: 1rem;
}

.content {
    flex: 1;
    padding: 32px 40px;
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* === Cards === */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    overflow: hidden;
    transition: var(--transition-normal);
}

.card:hover {
    border-color: var(--border-light);
}

.card-header {
    padding: 24px;
    border-bottom: 1px solid var(--border-color);
}

.card-header h2 {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 4px;
}

.card-header p {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.header-with-action {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.card-body {
    padding: 24px;
}

/* === Forms === */
.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    font-size: 0.9rem;
    font-weight: 500;
    margin-bottom: 8px;
    color: var(--text-secondary);
}

textarea,
input[type="text"] {
    width: 100%;
    padding: 14px 16px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-family: inherit;
    font-size: 0.95rem;
    resize: vertical;
    transition: var(--transition-fast);
}

textarea:focus,
input[type="text"]:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px var(--accent-glow);
}

textarea::placeholder,
input[type="text"]::placeholder {
    color: var(--text-muted);
}

.input-group {
    display: flex;
    align-items: stretch;
}

.input-prefix {
    padding: 14px 16px;
    background: var(--bg-hover);
    border: 1px solid var(--border-color);
    border-right: none;
    border-radius: var(--radius-md) 0 0 var(--radius-md);
    color: var(--text-muted);
    font-size: 0.9rem;
    display: flex;
    align-items: center;
}

.input-group input {
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

/* === Buttons === */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 14px 24px;
    border: none;
    border-radius: var(--radius-md);
    font-family: inherit;
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    transition: var(--transition-normal);
}

.btn svg {
    width: 18px;
    height: 18px;
}

.btn-primary {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    color: white;
    box-shadow: 0 4px 15px var(--accent-glow);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px var(--accent-glow);
}

.btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
}

.btn-secondary {
    background: var(--bg-hover);
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
}

.btn-secondary:hover {
    background: var(--border-light);
    color: var(--text-primary);
}

.btn-icon {
    padding: 8px;
    background: transparent;
    color: var(--text-muted);
}

.btn-icon:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
}

/* === Upload Zone === */
.upload-zone {
    border: 2px dashed var(--border-light);
    border-radius: var(--radius-lg);
    padding: 40px;
    text-align: center;
    transition: var(--transition-normal);
    cursor: pointer;
    margin-bottom: 20px;
    position: relative;
}

.upload-zone:hover,
.upload-zone.dragover {
    border-color: var(--accent-primary);
    background: rgba(6, 182, 212, 0.05);
}

.upload-content svg {
    width: 48px;
    height: 48px;
    color: var(--text-muted);
    margin-bottom: 16px;
}

.upload-content p {
    color: var(--text-secondary);
    margin-bottom: 8px;
}

.upload-content p span {
    color: var(--accent-secondary);
    text-decoration: underline;
    cursor: pointer;
}

.upload-content small {
    color: var(--text-muted);
    font-size: 0.85rem;
}

.preview-container {
    position: relative;
    display: inline-block;
}

.preview-container img {
    max-width: 100%;
    max-height: 300px;
    border-radius: var(--radius-md);
    object-fit: contain;
}

.remove-btn {
    position: absolute;
    top: -10px;
    right: -10px;
    width: 28px;
    height: 28px;
    background: var(--error);
    color: white;
    border: none;
    border-radius: 50%;
    font-size: 18px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: var(--transition-fast);
}

.remove-btn:hover {
    transform: scale(1.1);
}

/* === Tab Content === */
.tab-content {
    display: none;
    animation: fadeIn 0.3s ease;
}

.tab-content.active {
    display: block;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* === Results Section === */
.results-section {
    animation: slideUp 0.3s ease;
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.results-card {
    border-color: var(--accent-primary);
    box-shadow: 0 0 30px var(--accent-glow);
}

.result-block {
    margin-bottom: 24px;
    padding: 20px;
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    border-left: 3px solid var(--accent-primary);
}

.result-block:last-child {
    margin-bottom: 0;
}

.result-block h3 {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 12px;
    color: var(--accent-secondary);
    display: flex;
    align-items: center;
    gap: 8px;
}

.result-block h3 svg {
    width: 18px;
    height: 18px;
}

.result-block ul {
    list-style: none;
    padding: 0;
}

.result-block li {
    position: relative;
    padding-left: 20px;
    margin-bottom: 8px;
    color: var(--text-secondary);
    line-height: 1.5;
}

.result-block li::before {
    content: '→';
    position: absolute;
    left: 0;
    color: var(--accent-primary);
}

.result-block p {
    color: var(--text-secondary);
    line-height: 1.6;
}

.result-summary {
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(139, 92, 246, 0.1));
    border-left-color: var(--accent-secondary);
}

.result-summary p {
    font-size: 1.05rem;
    color: var(--text-primary);
}

/* Score indicator */
.score-display {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
}

.score-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent-secondary);
    font-family: var(--font-mono);
}

.score-label {
    color: var(--text-muted);
    font-size: 0.9rem;
}

.score-bar {
    flex: 1;
    height: 8px;
    background: var(--bg-input);
    border-radius: 4px;
    overflow: hidden;
}

.score-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
    border-radius: 4px;
    transition: width 0.5s ease;
}

/* Parsed content display */
.parsed-content {
    background: var(--bg-input);
    padding: 16px;
    border-radius: var(--radius-md);
    margin-bottom: 20px;
    font-family: var(--font-mono);
    font-size: 0.85rem;
}

.parsed-content .label {
    color: var(--accent-primary);
    font-weight: 500;
}

.parsed-content .value {
    color: var(--text-secondary);
    margin-bottom: 8px;
    padding-left: 12px;
}

/* === History === */
.history-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.history-empty {
    text-align: center;
    padding: 40px;
    color: var(--text-muted);
}

.history-empty svg {
    width: 48px;
    height: 48px;
    margin-bottom: 12px;
    opacity: 0.5;
}

.history-item {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 16px;
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
    transition: var(--transition-fast);
}

.history-item:hover {
    border-color: var(--border-light);
}

.history-icon {
    width: 40px;
    height: 40px;
    background: var(--bg-hover);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.history-icon svg {
    width: 20px;
    height: 20px;
    color: var(--accent-primary);
}

.history-content {
    flex: 1;
    min-width: 0;
}

.history-type {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--accent-secondary);
    margin-bottom: 4px;
}

.history-summary {
    color: var(--text-secondary);
    font-size: 0.9rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.history-time {
    color: var(--text-muted);
    font-size: 0.8rem;
    white-space: nowrap;
}

/* === Loading Overlay === */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(10, 15, 28, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(4px);
}

.loading-spinner {
    text-align: center;
}

.spinner {
    width: 60px;
    height: 60px;
    border: 3px solid var(--border-color);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.loading-spinner p {
    color: var(--text-secondary);
    font-size: 1rem;
}

/* === Responsive === */
@media (max-width: 1024px) {
    .sidebar {
        width: 80px;
    }
    
    .logo span,
    .nav-btn span,
    .sidebar-footer span {
        display: none;
    }
    
    .nav-btn {
        justify-content: center;
        padding: 14px;
    }
    
    .main {
        margin-left: 80px;
    }
    
    .content {
        padding: 24px;
    }
}

@media (max-width: 768px) {
    .sidebar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        top: auto;
        width: 100%;
        height: auto;
        flex-direction: row;
        border-right: none;
        border-top: 1px solid var(--border-color);
    }
    
    .logo,
    .sidebar-footer {
        display: none;
    }
    
    .nav {
        flex-direction: row;
        padding: 8px;
        justify-content: space-around;
    }
    
    .nav-btn {
        flex-direction: column;
        gap: 4px;
        padding: 12px 8px;
        font-size: 0.7rem;
    }
    
    .nav-btn svg {
        width: 24px;
        height: 24px;
    }
    
    .main {
        margin-left: 0;
        margin-bottom: 80px;
    }
    
    .header {
        padding: 20px;
    }
    
    .page-title {
        font-size: 1.5rem;
    }
    
    .content {
        padding: 16px;
    }
}

/* === Error State === */
.error-message {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid var(--error);
    border-radius: var(--radius-md);
    padding: 16px;
    color: var(--error);
    display: flex;
    align-items: center;
    gap: 12px;
}

.error-message svg {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
}

```

```javascript
/**
 * Competitor Monitor - Frontend Application
 * Мониторинг конкурентов - MVP ассистент
 */

// === State ===
const state = {
    currentTab: 'text',
    selectedImage: null,
    isLoading: false
};

// === DOM Elements ===
const elements = {
    // Navigation
    navButtons: document.querySelectorAll('.nav-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Text analysis
    competitorText: document.getElementById('competitor-text'),
    analyzeTextBtn: document.getElementById('analyze-text-btn'),
    
    // Image analysis
    uploadZone: document.getElementById('upload-zone'),
    imageInput: document.getElementById('image-input'),
    previewContainer: document.getElementById('preview-container'),
    imagePreview: document.getElementById('image-preview'),
    removeImageBtn: document.getElementById('remove-image'),
    analyzeImageBtn: document.getElementById('analyze-image-btn'),
    
    // Parse demo
    urlInput: document.getElementById('url-input'),
    parseBtn: document.getElementById('parse-btn'),
    
    // History
    historyList: document.getElementById('history-list'),
    clearHistoryBtn: document.getElementById('clear-history-btn'),
    
    // Results
    resultsSection: document.getElementById('results-section'),
    resultsContent: document.getElementById('results-content'),
    closeResultsBtn: document.getElementById('close-results'),
    
    // Loading
    loadingOverlay: document.getElementById('loading-overlay')
};

// === API Functions ===
const api = {
    baseUrl: '',
    
    async analyzeText(text) {
        const response = await fetch(`${this.baseUrl}/analyze_text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        return response.json();
    },
    
    async analyzeImage(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.baseUrl}/analyze_image`, {
            method: 'POST',
            body: formData
        });
        return response.json();
    },
    
    async parseDemo(url) {
        const response = await fetch(`${this.baseUrl}/parse_demo`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        return response.json();
    },
    
    async getHistory() {
        const response = await fetch(`${this.baseUrl}/history`);
        return response.json();
    },
    
    async clearHistory() {
        const response = await fetch(`${this.baseUrl}/history`, {
            method: 'DELETE'
        });
        return response.json();
    }
};

// === UI Functions ===
const ui = {
    showLoading() {
        state.isLoading = true;
        elements.loadingOverlay.hidden = false;
    },
    
    hideLoading() {
        state.isLoading = false;
        elements.loadingOverlay.hidden = true;
    },
    
    showTab(tabId) {
        state.currentTab = tabId;
        
        // Update navigation
        elements.navButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });
        
        // Update content
        elements.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === `${tabId}-tab`);
        });
        
        // Load history if needed
        if (tabId === 'history') {
            this.loadHistory();
        }
    },
    
    showResults(html) {
        elements.resultsContent.innerHTML = html;
        elements.resultsSection.hidden = false;
        elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    },
    
    hideResults() {
        elements.resultsSection.hidden = true;
    },
    
    showError(message) {
        const html = `
            <div class="error-message">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <span>${message}</span>
            </div>
        `;
        this.showResults(html);
    },
    
    renderTextAnalysis(analysis) {
        return `
            ${this.renderResultBlock('Сильные стороны', analysis.strengths, 'strengths')}
            ${this.renderResultBlock('Слабые стороны', analysis.weaknesses, 'weaknesses')}
            ${this.renderResultBlock('Уникальные предложения', analysis.unique_offers, 'unique')}
            ${this.renderResultBlock('Рекомендации', analysis.recommendations, 'recommendations')}
            ${analysis.summary ? `
                <div class="result-block result-summary">
                    <h3>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                        </svg>
                        Резюме
                    </h3>
                    <p>${analysis.summary}</p>
                </div>
            ` : ''}
        `;
    },
    
    renderImageAnalysis(analysis) {
        const scorePercent = (analysis.visual_style_score / 10) * 100;
        
        return `
            <div class="result-block">
                <h3>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5"/>
                        <polyline points="21 15 16 10 5 21"/>
                    </svg>
                    Описание изображения
                </h3>
                <p>${analysis.description}</p>
            </div>
            
            <div class="result-block">
                <h3>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                    Оценка визуального стиля
                </h3>
                <div class="score-display">
                    <span class="score-value">${analysis.visual_style_score}/10</span>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${scorePercent}%"></div>
                    </div>
                </div>
                <p>${analysis.visual_style_analysis}</p>
            </div>
            
            ${this.renderResultBlock('Маркетинговые инсайты', analysis.marketing_insights, 'insights')}
            ${this.renderResultBlock('Рекомендации', analysis.recommendations, 'recommendations')}
        `;
    },
    
    renderParsedContent(data) {
        const parsed = data;
        
        return `
            <div class="parsed-content">
                <div class="label">URL:</div>
                <div class="value">${parsed.url}</div>
                
                <div class="label">Title:</div>
                <div class="value">${parsed.title || 'Не найден'}</div>
                
                <div class="label">H1:</div>
                <div class="value">${parsed.h1 || 'Не найден'}</div>
                
                <div class="label">Первый абзац:</div>
                <div class="value">${parsed.first_paragraph || 'Не найден'}</div>
            </div>
            
            ${parsed.analysis ? this.renderTextAnalysis(parsed.analysis) : ''}
        `;
    },
    
    renderResultBlock(title, items, type) {
        if (!items || items.length === 0) return '';
        
        const icons = {
            strengths: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
            weaknesses: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
            unique: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
            recommendations: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
            insights: '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>'
        };
        
        return `
            <div class="result-block">
                <h3>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        ${icons[type] || icons.recommendations}
                    </svg>
                    ${title}
                </h3>
                <ul>
                    ${items.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `;
    },
    
    async loadHistory() {
        try {
            const data = await api.getHistory();
            this.renderHistory(data.items);
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    },
    
    renderHistory(items) {
        if (!items || items.length === 0) {
            elements.historyList.innerHTML = `
                <div class="history-empty">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    <p>История пуста</p>
                </div>
            `;
            return;
        }
        
        const icons = {
            text: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
            image: '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
            parse: '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>'
        };
        
        const typeLabels = {
            text: 'Анализ текста',
            image: 'Анализ изображения',
            parse: 'Парсинг сайта'
        };
        
        elements.historyList.innerHTML = items.map(item => {
            const date = new Date(item.timestamp);
            const timeStr = date.toLocaleString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            return `
                <div class="history-item">
                    <div class="history-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            ${icons[item.request_type] || icons.text}
                        </svg>
                    </div>
                    <div class="history-content">
                        <div class="history-type">${typeLabels[item.request_type] || item.request_type}</div>
                        <div class="history-summary">${item.request_summary}</div>
                    </div>
                    <div class="history-time">${timeStr}</div>
                </div>
            `;
        }).join('');
    }
};

// === Event Handlers ===
const handlers = {
    // Navigation
    handleNavClick(e) {
        const btn = e.target.closest('.nav-btn');
        if (btn) {
            ui.showTab(btn.dataset.tab);
        }
    },
    
    // Text analysis
    async handleAnalyzeText() {
        const text = elements.competitorText.value.trim();
        
        if (text.length < 10) {
            ui.showError('Введите текст минимум 10 символов для анализа');
            return;
        }
        
        ui.showLoading();
        
        try {
            const result = await api.analyzeText(text);
            
            if (result.success && result.analysis) {
                ui.showResults(ui.renderTextAnalysis(result.analysis));
            } else {
                ui.showError(result.error || 'Произошла ошибка при анализе');
            }
        } catch (error) {
            ui.showError('Ошибка соединения с сервером');
            console.error(error);
        } finally {
            ui.hideLoading();
        }
    },
    
    // Image upload
    handleUploadClick() {
        elements.imageInput.click();
    },
    
    handleImageSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processImage(file);
        }
    },
    
    handleDragOver(e) {
        e.preventDefault();
        elements.uploadZone.classList.add('dragover');
    },
    
    handleDragLeave(e) {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');
    },
    
    handleDrop(e) {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');
        
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            this.processImage(file);
        }
    },
    
    processImage(file) {
        state.selectedImage = file;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            elements.imagePreview.src = e.target.result;
            elements.previewContainer.hidden = false;
            elements.uploadZone.querySelector('.upload-content').hidden = true;
            elements.analyzeImageBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    },
    
    handleRemoveImage() {
        state.selectedImage = null;
        elements.imageInput.value = '';
        elements.imagePreview.src = '';
        elements.previewContainer.hidden = true;
        elements.uploadZone.querySelector('.upload-content').hidden = false;
        elements.analyzeImageBtn.disabled = true;
    },
    
    async handleAnalyzeImage() {
        if (!state.selectedImage) {
            ui.showError('Выберите изображение для анализа');
            return;
        }
        
        ui.showLoading();
        
        try {
            const result = await api.analyzeImage(state.selectedImage);
            
            if (result.success && result.analysis) {
                ui.showResults(ui.renderImageAnalysis(result.analysis));
            } else {
                ui.showError(result.error || 'Произошла ошибка при анализе изображения');
            }
        } catch (error) {
            ui.showError('Ошибка соединения с сервером');
            console.error(error);
        } finally {
            ui.hideLoading();
        }
    },
    
    // Parse demo
    async handleParse() {
        let url = elements.urlInput.value.trim();
        
        if (!url) {
            ui.showError('Введите URL сайта для парсинга');
            return;
        }
        
        // Add protocol if missing
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            url = 'https://' + url;
        }
        
        ui.showLoading();
        
        try {
            const result = await api.parseDemo(url);
            
            if (result.success && result.data) {
                ui.showResults(ui.renderParsedContent(result.data));
            } else {
                ui.showError(result.error || 'Не удалось распарсить сайт');
            }
        } catch (error) {
            ui.showError('Ошибка соединения с сервером');
            console.error(error);
        } finally {
            ui.hideLoading();
        }
    },
    
    // History
    async handleClearHistory() {
        if (!confirm('Вы уверены, что хотите очистить историю?')) {
            return;
        }
        
        try {
            await api.clearHistory();
            ui.renderHistory([]);
        } catch (error) {
            console.error('Failed to clear history:', error);
        }
    },
    
    // Results
    handleCloseResults() {
        ui.hideResults();
    }
};

// === Initialize ===
function init() {
    // Navigation
    elements.navButtons.forEach(btn => {
        btn.addEventListener('click', handlers.handleNavClick.bind(handlers));
    });
    
    // Text analysis
    elements.analyzeTextBtn.addEventListener('click', handlers.handleAnalyzeText.bind(handlers));
    
    // Image upload
    elements.uploadZone.addEventListener('click', handlers.handleUploadClick.bind(handlers));
    elements.imageInput.addEventListener('change', handlers.handleImageSelect.bind(handlers));
    elements.uploadZone.addEventListener('dragover', handlers.handleDragOver.bind(handlers));
    elements.uploadZone.addEventListener('dragleave', handlers.handleDragLeave.bind(handlers));
    elements.uploadZone.addEventListener('drop', handlers.handleDrop.bind(handlers));
    elements.removeImageBtn.addEventListener('click', handlers.handleRemoveImage.bind(handlers));
    elements.analyzeImageBtn.addEventListener('click', handlers.handleAnalyzeImage.bind(handlers));
    
    // Parse demo
    elements.parseBtn.addEventListener('click', handlers.handleParse.bind(handlers));
    elements.urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handlers.handleParse.call(handlers);
    });
    
    // History
    elements.clearHistoryBtn.addEventListener('click', handlers.handleClearHistory.bind(handlers));
    
    // Results
    elements.closeResultsBtn.addEventListener('click', handlers.handleCloseResults.bind(handlers));
    
    // Show default tab
    ui.showTab('text');
}

// Start app
document.addEventListener('DOMContentLoaded', init);

```

```plaintext
# OpenAI API Configuration
# Скопируйте этот файл как .env и заполните данные

OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o-mini

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

```

```markdown
# 🔍 Мониторинг конкурентов - AI Ассистент

MVP приложение для анализа конкурентной среды с поддержкой мультимодальности (текст и изображения).

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-purple.svg)

## 📋 Описание

Приложение позволяет:
- **Анализировать текст конкурентов** — получать структурированную аналитику с сильными/слабыми сторонами, уникальными предложениями и рекомендациями
- **Анализировать изображения** — баннеры, скриншоты сайтов, упаковки товаров с оценкой визуального стиля
- **Парсить сайты** — автоматически извлекать и анализировать контент по URL
- **Хранить историю** — последние 10 запросов сохраняются для быстрого доступа

## 🚀 Быстрый старт

### 1. Клонирование и установка зависимостей

```bash
# Клонируйте репозиторий
cd competitor-monitor

# Создайте виртуальное окружение
python -m venv venv

# Активируйте окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта (используйте `env.example.txt` как шаблон):

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o-mini
```

### 3. Запуск приложения

```bash
# Запуск сервера
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Приложение будет доступно по адресу: http://localhost:8000

## 📁 Структура проекта

```
competitor-monitor/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI приложение
│   ├── config.py            # Конфигурация
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic модели
│   └── services/
│       ├── __init__.py
│       ├── openai_service.py    # Работа с OpenAI API
│       ├── parser_service.py    # Парсинг веб-страниц
│       └── history_service.py   # Управление историей
├── frontend/
│   ├── index.html           # HTML страница
│   ├── styles.css           # Стили
│   └── app.js               # JavaScript логика
├── requirements.txt         # Зависимости Python
├── env.example.txt          # Пример .env файла
├── history.json             # Файл истории (создаётся автоматически)
├── README.md                # Этот файл
└── docs.md                  # Документация API
```

## 🔧 Функциональность

### Анализ текста (`/analyze_text`)
- Принимает текст конкурента (минимум 10 символов)
- Возвращает:
  - Сильные стороны
  - Слабые стороны
  - Уникальные предложения
  - Рекомендации по улучшению
  - Общее резюме

### Анализ изображений (`/analyze_image`)
- Принимает изображения: PNG, JPG, GIF, WEBP
- Возвращает:
  - Описание изображения
  - Маркетинговые инсайты
  - Оценку визуального стиля (0-10)
  - Рекомендации

### Парсинг сайтов (`/parse_demo`)
- Принимает URL сайта
- Извлекает: title, h1, первый абзац
- Автоматически анализирует извлечённый контент

### История (`/history`)
- Хранит последние 10 запросов
- Сохраняет тип запроса, краткое описание, время

## 🛠️ Технологии

- **Backend**: FastAPI, Python 3.9+
- **AI**: OpenAI GPT-4o-mini (или GPT-4.1)
- **Frontend**: Vanilla JS, CSS3
- **Парсинг**: BeautifulSoup4, httpx
- **Валидация**: Pydantic

## 📖 API Документация

После запуска сервера доступна интерактивная документация:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Подробная документация API в файле [docs.md](docs.md)

## ⚠️ Требования

- Python 3.9+
- OpenAI API ключ с доступом к GPT-4o-mini или GPT-4.1
- Интернет-соединение для работы AI и парсинга

## 📝 Лицензия

MIT License

```

```markdown
# 📚 Документация API - Мониторинг конкурентов

## Содержание

1. [Структура проекта](#структура-проекта)
2. [Описание API](#описание-api)
3. [Примеры запросов](#примеры-запросов)
4. [Мультимодальные функции](#мультимодальные-функции)
5. [Модели данных](#модели-данных)

---

## Структура проекта

```
competitor-monitor/
│
├── backend/                     # Backend модуль
│   ├── __init__.py
│   ├── main.py                  # Главный файл FastAPI
│   ├── config.py                # Конфигурация приложения
│   │
│   ├── models/                  # Pydantic модели
│   │   ├── __init__.py
│   │   └── schemas.py           # Схемы запросов/ответов
│   │
│   └── services/                # Бизнес-логика
│       ├── __init__.py
│       ├── openai_service.py    # Интеграция с OpenAI
│       ├── parser_service.py    # Парсинг веб-страниц
│       └── history_service.py   # Управление историей
│
├── frontend/                    # Frontend модуль
│   ├── index.html               # Главная HTML страница
│   ├── styles.css               # CSS стили
│   └── app.js                   # JavaScript приложение
│
├── requirements.txt             # Python зависимости
├── env.example.txt              # Пример переменных окружения
├── history.json                 # Файл истории запросов
├── README.md                    # Описание проекта
└── docs.md                      # Эта документация
```

---

## Описание API

### Базовый URL

```
http://localhost:8000
```

### Эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Главная страница (веб-интерфейс) |
| POST | `/analyze_text` | Анализ текста конкурента |
| POST | `/analyze_image` | Анализ изображения конкурента |
| POST | `/parse_demo` | Парсинг и анализ сайта по URL |
| GET | `/history` | Получение истории запросов |
| DELETE | `/history` | Очистка истории запросов |
| GET | `/health` | Проверка работоспособности |
| GET | `/docs` | Swagger UI документация |
| GET | `/redoc` | ReDoc документация |

---

## Примеры запросов

### 1. Анализ текста (`POST /analyze_text`)

**Запрос:**
```bash
curl -X POST "http://localhost:8000/analyze_text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Наша компания предлагает уникальные решения для бизнеса. Мы работаем на рынке 10 лет и обслуживаем более 1000 клиентов. Наши преимущества: быстрая доставка, гарантия качества, индивидуальный подход к каждому клиенту."
  }'
```

**Ответ:**
```json
{
  "success": true,
  "analysis": {
    "strengths": [
      "Долгий опыт работы на рынке (10 лет)",
      "Большая клиентская база (1000+ клиентов)",
      "Комплексный подход к обслуживанию"
    ],
    "weaknesses": [
      "Отсутствие конкретных цен",
      "Нет упоминания о технологиях",
      "Общие формулировки без специфики"
    ],
    "unique_offers": [
      "Индивидуальный подход к каждому клиенту",
      "Гарантия качества"
    ],
    "recommendations": [
      "Добавить конкретные цифры и кейсы",
      "Указать уникальные технологические преимущества",
      "Включить отзывы клиентов"
    ],
    "summary": "Компания позиционирует себя как надёжного партнёра с опытом, но маркетинговые материалы требуют конкретизации для повышения конверсии."
  },
  "error": null
}
```

### 2. Анализ изображения (`POST /analyze_image`)

**Запрос:**
```bash
curl -X POST "http://localhost:8000/analyze_image" \
  -F "file=@banner.jpg"
```

**Ответ:**
```json
{
  "success": true,
  "analysis": {
    "description": "Рекламный баннер с изображением продукта на синем градиентном фоне. Крупный заголовок белым шрифтом, кнопка CTA оранжевого цвета.",
    "marketing_insights": [
      "Чёткая визуальная иерархия привлекает внимание",
      "Контрастная цветовая схема выделяет CTA",
      "Минималистичный дизайн не перегружает восприятие"
    ],
    "visual_style_score": 7,
    "visual_style_analysis": "Современный корпоративный стиль с хорошим балансом элементов. Типографика читабельна, но можно улучшить отступы.",
    "recommendations": [
      "Добавить социальное доказательство (отзывы, рейтинги)",
      "Увеличить размер CTA кнопки",
      "Рассмотреть A/B тестирование цветов"
    ]
  },
  "error": null
}
```

### 3. Парсинг сайта (`POST /parse_demo`)

**Запрос:**
```bash
curl -X POST "http://localhost:8000/parse_demo" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "example.com"
  }'
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "title": "Example Domain",
    "h1": "Example Domain",
    "first_paragraph": "This domain is for use in illustrative examples in documents.",
    "analysis": {
      "strengths": ["..."],
      "weaknesses": ["..."],
      "unique_offers": ["..."],
      "recommendations": ["..."],
      "summary": "..."
    }
  },
  "error": null
}
```

### 4. Получение истории (`GET /history`)

**Запрос:**
```bash
curl -X GET "http://localhost:8000/history"
```

**Ответ:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-01-15T10:30:00",
      "request_type": "text",
      "request_summary": "Наша компания предлагает уникальные решения...",
      "response_summary": "Компания позиционирует себя как надёжного партнёра..."
    }
  ],
  "total": 1
}
```

### 5. Очистка истории (`DELETE /history`)

**Запрос:**
```bash
curl -X DELETE "http://localhost:8000/history"
```

**Ответ:**
```json
{
  "success": true,
  "message": "История очищена"
}
```

### 6. Проверка здоровья (`GET /health`)

**Запрос:**
```bash
curl -X GET "http://localhost:8000/health"
```

**Ответ:**
```json
{
  "status": "healthy",
  "service": "Competitor Monitor",
  "version": "1.0.0"
}
```

---

## Мультимодальные функции

### Поддержка текста

Приложение анализирует любой текстовый контент конкурентов:
- Описания продуктов
- Тексты с лендингов
- Рекламные объявления
- Посты в социальных сетях
- Email рассылки

**Минимальная длина текста:** 10 символов

### Поддержка изображений

Поддерживаемые форматы:
- JPEG/JPG
- PNG
- GIF
- WebP

**Что можно анализировать:**
- Рекламные баннеры
- Скриншоты сайтов
- Фотографии упаковки
- Креативы для социальных сетей
- Логотипы и фирменный стиль

**Максимальный размер:** 10MB (рекомендуется до 4MB для быстрой обработки)

### Парсинг веб-страниц

Автоматически извлекаемые элементы:
- `<title>` — заголовок страницы
- `<h1>` — главный заголовок
- Первый значимый `<p>` — первый абзац (минимум 50 символов)

**Особенности:**
- Автоматическое добавление протокола `https://`
- Следование редиректам
- Таймаут: 10 секунд
- User-Agent: Mozilla/5.0 (имитация браузера)

---

## Модели данных

### TextAnalysisRequest
```typescript
{
  text: string  // Минимум 10 символов
}
```

### ParseDemoRequest
```typescript
{
  url: string  // URL сайта для парсинга
}
```

### CompetitorAnalysis
```typescript
{
  strengths: string[]      // Сильные стороны
  weaknesses: string[]     // Слабые стороны
  unique_offers: string[]  // Уникальные предложения
  recommendations: string[] // Рекомендации
  summary: string          // Общее резюме
}
```

### ImageAnalysis
```typescript
{
  description: string           // Описание изображения
  marketing_insights: string[]  // Маркетинговые инсайты
  visual_style_score: number    // Оценка 0-10
  visual_style_analysis: string // Анализ стиля
  recommendations: string[]     // Рекомендации
}
```

### HistoryItem
```typescript
{
  id: string              // UUID записи
  timestamp: datetime     // Время запроса
  request_type: string    // "text" | "image" | "parse"
  request_summary: string // Краткое описание запроса
  response_summary: string // Краткое описание ответа
}
```

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 400 | Некорректный запрос (неверный формат, короткий текст) |
| 422 | Ошибка валидации данных |
| 500 | Внутренняя ошибка сервера |

---

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `OPENAI_API_KEY` | API ключ OpenAI | - |
| `OPENAI_MODEL` | Модель для текста | `gpt-4o-mini` |
| `OPENAI_VISION_MODEL` | Модель для изображений | `gpt-4o-mini` |
| `API_HOST` | Хост сервера | `0.0.0.0` |
| `API_PORT` | Порт сервера | `8000` |

### Настройки истории

- Максимум записей: **10**
- Файл хранения: `history.json`
- Формат: JSON с UTF-8 кодировкой

---

## Безопасность

⚠️ **Важно:**
- Не храните API ключи в коде
- Используйте `.env` файл для секретов
- Добавьте `.env` в `.gitignore`
- В продакшене используйте HTTPS
- Настройте CORS для конкретных доменов

```

```json
[]

```

```python
"""
Скрипт запуска приложения Мониторинг конкурентов
"""
import uvicorn
from backend.config import settings

if __name__ == "__main__":
    print("🚀 Запуск сервера Мониторинг конкурентов...")
    print(f"📍 Адрес: http://localhost:{settings.api_port}")
    print(f"📚 Документация: http://localhost:{settings.api_port}/docs")
    print("-" * 50)
    
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

```

Готово! Я создал полнофункциональное мультимодальное приложение **"Мониторинг конкурентов"**. 

## 📁 Структура проекта

```
competitor-monitor/
├── backend/
│   ├── main.py              # FastAPI приложение с 5 эндпоинтами
│   ├── config.py            # Конфигурация OpenAI и сервера
│   ├── models/schemas.py    # Pydantic модели данных
│   └── services/
│       ├── openai_service.py    # Анализ текста и изображений через GPT-4
│       ├── parser_service.py    # Парсинг веб-страниц
│       └── history_service.py   # История запросов (JSON)
├── frontend/
│   ├── index.html           # Современный веб-интерфейс
│   ├── styles.css           # Тёмная тема с cyan акцентами
│   └── app.js               # JavaScript логика
├── requirements.txt         # Python зависимости
├── run.py                   # Скрипт запуска
├── README.md                # Описание проекта
└── docs.md                  # Документация API
```

## 🚀 Как запустить

```powershell
# 1. Создайте виртуальное окружение
python -m venv venv
venv\Scripts\activate

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Создайте файл .env с вашим API ключом OpenAI
# OPENAI_API_KEY=sk-your-key-here

# 4. Запустите сервер
python run.py
```

Приложение будет доступно на http://localhost:8000

## ✅ Реализованные функции

| Эндпоинт | Описание |
|----------|----------|
| `POST /analyze_text` | Анализ текста → сильные/слабые стороны, УТП, рекомендации |
| `POST /analyze_image` | Анализ изображений → описание, маркетинговые инсайты, оценка стиля |
| `POST /parse_demo` | Парсинг URL → title, h1, первый абзац + анализ |
| `GET /history` | Последние 10 запросов |
| `DELETE /history` | Очистка истории |

## 🎨 Веб-интерфейс

- Тёмная тема с градиентами
- Drag & Drop загрузка изображений
- Табы для разных функций
- Адаптивный дизайн
- Анимированные результаты

Документация Swagger доступна на http://localhost:8000/docs после запуска!

```plaintext
competitor-monitor/
├── backend/
│   ├── main.py              # FastAPI приложение с 5 эндпоинтами
│   ├── config.py            # Конфигурация OpenAI и сервера
│   ├── models/schemas.py    # Pydantic модели данных
│   └── services/
│       ├── openai_service.py    # Анализ текста и изображений через GPT-4
│       ├── parser_service.py    # Парсинг веб-страниц
│       └── history_service.py   # История запросов (JSON)
├── frontend/
│   ├── index.html           # Современный веб-интерфейс
│   ├── styles.css           # Тёмная тема с cyan акцентами
│   └── app.js               # JavaScript логика
├── requirements.txt         # Python зависимости
├── run.py                   # Скрипт запуска
├── README.md                # Описание проекта
└── docs.md                  # Документация API
```

```powershell
# 1. Создайте виртуальное окружение
python -m venv venv
venv\Scripts\activate

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Создайте файл .env с вашим API ключом OpenAI
# OPENAI_API_KEY=sk-your-key-here

# 4. Запустите сервер
python run.py
```

---

**User**

@pip (0-70) 

---

**Cursor**

Вижу ошибку с установкой Pillow. Эта версия (10.1.0) устарела и не совместима с вашей версией Python. Обновлю зависимости:

```pip-requirements
fastapi>=0.104.0
uvicorn>=0.24.0
openai>=1.6.0
httpx>=0.25.0
python-multipart>=0.0.6
beautifulsoup4>=4.12.0
lxml>=5.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
aiofiles>=23.2.0
Pillow>=10.0.0


```

Обновил `requirements.txt` — теперь используются гибкие версии, совместимые с вашим Python. Запустите установку заново:

Обновил `requirements.txt`. Выполните команду вручную:

```powershell
pip install -r requirements.txt
```

После успешной установки запустите сервер:

```powershell
python run.py
```

```powershell
pip install -r requirements.txt
```

```powershell
python run.py
```

---

**User**

Зашёл на сайт, там висит анализирование данных

---

**Cursor**

Проверю терминал на наличие ошибок:

```css
[hidden] {
    display: none !important;
}
```

Вижу проблему! Loading overlay не скрывается из-за CSS. Атрибут `hidden` не работает с `display: flex`. Исправлю:

```css
/* === Variables === */
:root {
    /* Colors - Dark theme with cyan accents */
    --bg-primary: #0a0f1c;
    --bg-secondary: #111827;
    --bg-card: #1a2234;
    --bg-hover: #243049;
    --bg-input: #0d1320;
    
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    
    --accent-primary: #06b6d4;
    --accent-secondary: #22d3ee;
    --accent-glow: rgba(6, 182, 212, 0.3);
    
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    
    --border-color: #1e293b;
    --border-light: #334155;
    
    /* Typography */
    --font-primary: 'Outfit', -apple-system, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    
    /* Spacing */
    --sidebar-width: 280px;
    --header-height: 80px;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    
    /* Transitions */
    --transition-fast: 150ms ease;
    --transition-normal: 250ms ease;
}

/* === Reset & Base === */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

[hidden] {
    display: none !important;
}

html {
    font-size: 16px;
    scroll-behavior: smooth;
}

body {
    font-family: var(--font-primary);
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
    overflow-x: hidden;
}

/* Background pattern */
body::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(6, 182, 212, 0.15), transparent),
        radial-gradient(ellipse 60% 40% at 100% 100%, rgba(139, 92, 246, 0.1), transparent);
    pointer-events: none;
    z-index: -1;
}

/* === App Layout === */
.app {
    display: flex;
    min-height: 100vh;
}

/* === Sidebar === */
.sidebar {
    width: var(--sidebar-width);
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    position: fixed;
    height: 100vh;
    z-index: 100;
}

.logo {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 24px;
    border-bottom: 1px solid var(--border-color);
}

.logo-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 15px var(--accent-glow);
}

.logo-icon svg {
    width: 24px;
    height: 24px;
    color: white;
}

.logo span {
    font-size: 1.25rem;
    font-weight: 600;
    background: linear-gradient(135deg, var(--text-primary), var(--accent-secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.nav {
    flex: 1;
    padding: 16px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.nav-btn {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    padding: 14px 16px;
    background: transparent;
    border: none;
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    font-family: inherit;
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    transition: var(--transition-normal);
    text-align: left;
}

.nav-btn svg {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
}

.nav-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
}

.nav-btn.active {
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(6, 182, 212, 0.1));
    color: var(--accent-secondary);
    box-shadow: inset 0 0 0 1px rgba(6, 182, 212, 0.3);
}

.sidebar-footer {
    padding: 16px 24px;
    border-top: 1px solid var(--border-color);
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: var(--text-muted);
}

.status-dot {
    width: 8px;
    height: 8px;
    background: var(--success);
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* === Main Content === */
.main {
    flex: 1;
    margin-left: var(--sidebar-width);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.header {
    padding: 32px 40px;
    border-bottom: 1px solid var(--border-color);
    background: rgba(17, 24, 39, 0.5);
    backdrop-filter: blur(10px);
}

.page-title {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 8px;
    background: linear-gradient(135deg, var(--text-primary), var(--accent-secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.page-subtitle {
    color: var(--text-secondary);
    font-size: 1rem;
}

.content {
    flex: 1;
    padding: 32px 40px;
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* === Cards === */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    overflow: hidden;
    transition: var(--transition-normal);
}

.card:hover {
    border-color: var(--border-light);
}

.card-header {
    padding: 24px;
    border-bottom: 1px solid var(--border-color);
}

.card-header h2 {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 4px;
}

.card-header p {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.header-with-action {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.card-body {
    padding: 24px;
}

/* === Forms === */
.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    font-size: 0.9rem;
    font-weight: 500;
    margin-bottom: 8px;
    color: var(--text-secondary);
}

textarea,
input[type="text"] {
    width: 100%;
    padding: 14px 16px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-family: inherit;
    font-size: 0.95rem;
    resize: vertical;
    transition: var(--transition-fast);
}

textarea:focus,
input[type="text"]:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px var(--accent-glow);
}

textarea::placeholder,
input[type="text"]::placeholder {
    color: var(--text-muted);
}

.input-group {
    display: flex;
    align-items: stretch;
}

.input-prefix {
    padding: 14px 16px;
    background: var(--bg-hover);
    border: 1px solid var(--border-color);
    border-right: none;
    border-radius: var(--radius-md) 0 0 var(--radius-md);
    color: var(--text-muted);
    font-size: 0.9rem;
    display: flex;
    align-items: center;
}

.input-group input {
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

/* === Buttons === */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 14px 24px;
    border: none;
    border-radius: var(--radius-md);
    font-family: inherit;
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    transition: var(--transition-normal);
}

.btn svg {
    width: 18px;
    height: 18px;
}

.btn-primary {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    color: white;
    box-shadow: 0 4px 15px var(--accent-glow);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px var(--accent-glow);
}

.btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
}

.btn-secondary {
    background: var(--bg-hover);
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
}

.btn-secondary:hover {
    background: var(--border-light);
    color: var(--text-primary);
}

.btn-icon {
    padding: 8px;
    background: transparent;
    color: var(--text-muted);
}

.btn-icon:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
}

/* === Upload Zone === */
.upload-zone {
    border: 2px dashed var(--border-light);
    border-radius: var(--radius-lg);
    padding: 40px;
    text-align: center;
    transition: var(--transition-normal);
    cursor: pointer;
    margin-bottom: 20px;
    position: relative;
}

.upload-zone:hover,
.upload-zone.dragover {
    border-color: var(--accent-primary);
    background: rgba(6, 182, 212, 0.05);
}

.upload-content svg {
    width: 48px;
    height: 48px;
    color: var(--text-muted);
    margin-bottom: 16px;
}

.upload-content p {
    color: var(--text-secondary);
    margin-bottom: 8px;
}

.upload-content p span {
    color: var(--accent-secondary);
    text-decoration: underline;
    cursor: pointer;
}

.upload-content small {
    color: var(--text-muted);
    font-size: 0.85rem;
}

.preview-container {
    position: relative;
    display: inline-block;
}

.preview-container img {
    max-width: 100%;
    max-height: 300px;
    border-radius: var(--radius-md);
    object-fit: contain;
}

.remove-btn {
    position: absolute;
    top: -10px;
    right: -10px;
    width: 28px;
    height: 28px;
    background: var(--error);
    color: white;
    border: none;
    border-radius: 50%;
    font-size: 18px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: var(--transition-fast);
}

.remove-btn:hover {
    transform: scale(1.1);
}

/* === Tab Content === */
.tab-content {
    display: none;
    animation: fadeIn 0.3s ease;
}

.tab-content.active {
    display: block;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* === Results Section === */
.results-section {
    animation: slideUp 0.3s ease;
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.results-card {
    border-color: var(--accent-primary);
    box-shadow: 0 0 30px var(--accent-glow);
}

.result-block {
    margin-bottom: 24px;
    padding: 20px;
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    border-left: 3px solid var(--accent-primary);
}

.result-block:last-child {
    margin-bottom: 0;
}

.result-block h3 {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 12px;
    color: var(--accent-secondary);
    display: flex;
    align-items: center;
    gap: 8px;
}

.result-block h3 svg {
    width: 18px;
    height: 18px;
}

.result-block ul {
    list-style: none;
    padding: 0;
}

.result-block li {
    position: relative;
    padding-left: 20px;
    margin-bottom: 8px;
    color: var(--text-secondary);
    line-height: 1.5;
}

.result-block li::before {
    content: '→';
    position: absolute;
    left: 0;
    color: var(--accent-primary);
}

.result-block p {
    color: var(--text-secondary);
    line-height: 1.6;
}

.result-summary {
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(139, 92, 246, 0.1));
    border-left-color: var(--accent-secondary);
}

.result-summary p {
    font-size: 1.05rem;
    color: var(--text-primary);
}

/* Score indicator */
.score-display {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
}

.score-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent-secondary);
    font-family: var(--font-mono);
}

.score-label {
    color: var(--text-muted);
    font-size: 0.9rem;
}

.score-bar {
    flex: 1;
    height: 8px;
    background: var(--bg-input);
    border-radius: 4px;
    overflow: hidden;
}

.score-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
    border-radius: 4px;
    transition: width 0.5s ease;
}

/* Parsed content display */
.parsed-content {
    background: var(--bg-input);
    padding: 16px;
    border-radius: var(--radius-md);
    margin-bottom: 20px;
    font-family: var(--font-mono);
    font-size: 0.85rem;
}

.parsed-content .label {
    color: var(--accent-primary);
    font-weight: 500;
}

.parsed-content .value {
    color: var(--text-secondary);
    margin-bottom: 8px;
    padding-left: 12px;
}

/* === History === */
.history-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.history-empty {
    text-align: center;
    padding: 40px;
    color: var(--text-muted);
}

.history-empty svg {
    width: 48px;
    height: 48px;
    margin-bottom: 12px;
    opacity: 0.5;
}

.history-item {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 16px;
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
    transition: var(--transition-fast);
}

.history-item:hover {
    border-color: var(--border-light);
}

.history-icon {
    width: 40px;
    height: 40px;
    background: var(--bg-hover);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.history-icon svg {
    width: 20px;
    height: 20px;
    color: var(--accent-primary);
}

.history-content {
    flex: 1;
    min-width: 0;
}

.history-type {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--accent-secondary);
    margin-bottom: 4px;
}

.history-summary {
    color: var(--text-secondary);
    font-size: 0.9rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.history-time {
    color: var(--text-muted);
    font-size: 0.8rem;
    white-space: nowrap;
}

/* === Loading Overlay === */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(10, 15, 28, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(4px);
}

.loading-spinner {
    text-align: center;
}

.spinner {
    width: 60px;
    height: 60px;
    border: 3px solid var(--border-color);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.loading-spinner p {
    color: var(--text-secondary);
    font-size: 1rem;
}

/* === Responsive === */
@media (max-width: 1024px) {
    .sidebar {
        width: 80px;
    }
    
    .logo span,
    .nav-btn span,
    .sidebar-footer span {
        display: none;
    }
    
    .nav-btn {
        justify-content: center;
        padding: 14px;
    }
    
    .main {
        margin-left: 80px;
    }
    
    .content {
        padding: 24px;
    }
}

@media (max-width: 768px) {
    .sidebar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        top: auto;
        width: 100%;
        height: auto;
        flex-direction: row;
        border-right: none;
        border-top: 1px solid var(--border-color);
    }
    
    .logo,
    .sidebar-footer {
        display: none;
    }
    
    .nav {
        flex-direction: row;
        padding: 8px;
        justify-content: space-around;
    }
    
    .nav-btn {
        flex-direction: column;
        gap: 4px;
        padding: 12px 8px;
        font-size: 0.7rem;
    }
    
    .nav-btn svg {
        width: 24px;
        height: 24px;
    }
    
    .main {
        margin-left: 0;
        margin-bottom: 80px;
    }
    
    .header {
        padding: 20px;
    }
    
    .page-title {
        font-size: 1.5rem;
    }
    
    .content {
        padding: 16px;
    }
}

/* === Error State === */
.error-message {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid var(--error);
    border-radius: var(--radius-md);
    padding: 16px;
    color: var(--error);
    display: flex;
    align-items: center;
    gap: 12px;
}

.error-message svg {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
}


```

Исправил! Обновите страницу (Ctrl+F5 для полной перезагрузки без кэша). Теперь loading overlay будет корректно скрываться.

---

**User**

Перехожу на http://127.0.0.1:8000/ 

На главном экране висит анализирую данных - и не прекращается

---

**Cursor**

Вижу проблему — сервер остановлен, а CSS/JS файлы не загружаются. Проверю настройки и перезапущу:

```plaintext
INFO:     127.0.0.1:63192 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:63191 - "GET /static/app.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:63192 - "GET /static/styles.css HTTP/1.1" 200 OK
```

```plaintext
INFO:     127.0.0.1:63296 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:63296 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:63296 - "GET / HTTP/1.1" 200 OK
```

Проблема в том, что CSS может не загружаться, и loading overlay виден. Добавлю inline стиль для гарантированного скрытия:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Мониторинг конкурентов | AI Ассистент</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="app">
        <!-- Sidebar -->
        <aside class="sidebar">
            <div class="logo">
                <div class="logo-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                </div>
                <span>CompetitorAI</span>
            </div>
            
            <nav class="nav">
                <button class="nav-btn active" data-tab="text">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                        <line x1="16" y1="13" x2="8" y2="13"/>
                        <line x1="16" y1="17" x2="8" y2="17"/>
                    </svg>
                    Анализ текста
                </button>
                <button class="nav-btn" data-tab="image">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5"/>
                        <polyline points="21 15 16 10 5 21"/>
                    </svg>
                    Анализ изображений
                </button>
                <button class="nav-btn" data-tab="parse">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="2" y1="12" x2="22" y2="12"/>
                        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                    </svg>
                    Парсинг сайта
                </button>
                <button class="nav-btn" data-tab="history">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    История
                </button>
            </nav>
            
            <div class="sidebar-footer">
                <div class="status-indicator">
                    <span class="status-dot"></span>
                    <span>Система активна</span>
                </div>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="main">
            <header class="header">
                <h1 class="page-title">Мониторинг конкурентов</h1>
                <p class="page-subtitle">AI-ассистент для анализа конкурентной среды</p>
            </header>

            <div class="content">
                <!-- Text Analysis Tab -->
                <section class="tab-content active" id="text-tab">
                    <div class="card">
                        <div class="card-header">
                            <h2>Анализ текста конкурента</h2>
                            <p>Вставьте текст с сайта конкурента, из рекламы или описания продукта</p>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                <label for="competitor-text">Текст для анализа</label>
                                <textarea 
                                    id="competitor-text" 
                                    placeholder="Вставьте текст конкурента для анализа...&#10;&#10;Например: описание продукта, текст с лендинга, рекламное объявление..."
                                    rows="8"
                                ></textarea>
                            </div>
                            <button class="btn btn-primary" id="analyze-text-btn">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                                </svg>
                                Проанализировать
                            </button>
                        </div>
                    </div>
                </section>

                <!-- Image Analysis Tab -->
                <section class="tab-content" id="image-tab">
                    <div class="card">
                        <div class="card-header">
                            <h2>Анализ изображений</h2>
                            <p>Загрузите скриншот сайта, баннер или фото упаковки конкурента</p>
                        </div>
                        <div class="card-body">
                            <div class="upload-zone" id="upload-zone">
                                <input type="file" id="image-input" accept="image/*" hidden>
                                <div class="upload-content">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                        <polyline points="17 8 12 3 7 8"/>
                                        <line x1="12" y1="3" x2="12" y2="15"/>
                                    </svg>
                                    <p>Перетащите изображение или <span>выберите файл</span></p>
                                    <small>PNG, JPG, GIF, WEBP до 10MB</small>
                                </div>
                                <div class="preview-container" id="preview-container" hidden>
                                    <img id="image-preview" alt="Preview">
                                    <button class="remove-btn" id="remove-image">×</button>
                                </div>
                            </div>
                            <button class="btn btn-primary" id="analyze-image-btn" disabled>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                                </svg>
                                Проанализировать
                            </button>
                        </div>
                    </div>
                </section>

                <!-- Parse Demo Tab -->
                <section class="tab-content" id="parse-tab">
                    <div class="card">
                        <div class="card-header">
                            <h2>Парсинг сайта конкурента</h2>
                            <p>Введите URL сайта для автоматического извлечения и анализа контента</p>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                <label for="url-input">URL сайта</label>
                                <div class="input-group">
                                    <span class="input-prefix">https://</span>
                                    <input 
                                        type="text" 
                                        id="url-input" 
                                        placeholder="example.com"
                                    >
                                </div>
                            </div>
                            <button class="btn btn-primary" id="parse-btn">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                                </svg>
                                Парсить и анализировать
                            </button>
                        </div>
                    </div>
                </section>

                <!-- History Tab -->
                <section class="tab-content" id="history-tab">
                    <div class="card">
                        <div class="card-header">
                            <div class="header-with-action">
                                <div>
                                    <h2>История запросов</h2>
                                    <p>Последние 10 запросов к системе</p>
                                </div>
                                <button class="btn btn-secondary" id="clear-history-btn">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="3 6 5 6 21 6"/>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                    </svg>
                                    Очистить
                                </button>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="history-list" id="history-list">
                                <div class="history-empty">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="12" cy="12" r="10"/>
                                        <polyline points="12 6 12 12 16 14"/>
                                    </svg>
                                    <p>История пуста</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Results Section -->
                <section class="results-section" id="results-section" hidden>
                    <div class="card results-card">
                        <div class="card-header">
                            <div class="header-with-action">
                                <h2>Результаты анализа</h2>
                                <button class="btn btn-icon" id="close-results">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <line x1="18" y1="6" x2="6" y2="18"/>
                                        <line x1="6" y1="6" x2="18" y2="18"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                        <div class="card-body">
                            <div id="results-content"></div>
                        </div>
                    </div>
                </section>
            </div>
        </main>
    </div>

    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loading-overlay" style="display: none;">
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Анализирую данные...</p>
        </div>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>


```

```javascript
/**
 * Competitor Monitor - Frontend Application
 * Мониторинг конкурентов - MVP ассистент
 */

// === State ===
const state = {
    currentTab: 'text',
    selectedImage: null,
    isLoading: false
};

// === DOM Elements ===
const elements = {
    // Navigation
    navButtons: document.querySelectorAll('.nav-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Text analysis
    competitorText: document.getElementById('competitor-text'),
    analyzeTextBtn: document.getElementById('analyze-text-btn'),
    
    // Image analysis
    uploadZone: document.getElementById('upload-zone'),
    imageInput: document.getElementById('image-input'),
    previewContainer: document.getElementById('preview-container'),
    imagePreview: document.getElementById('image-preview'),
    removeImageBtn: document.getElementById('remove-image'),
    analyzeImageBtn: document.getElementById('analyze-image-btn'),
    
    // Parse demo
    urlInput: document.getElementById('url-input'),
    parseBtn: document.getElementById('parse-btn'),
    
    // History
    historyList: document.getElementById('history-list'),
    clearHistoryBtn: document.getElementById('clear-history-btn'),
    
    // Results
    resultsSection: document.getElementById('results-section'),
    resultsContent: document.getElementById('results-content'),
    closeResultsBtn: document.getElementById('close-results'),
    
    // Loading
    loadingOverlay: document.getElementById('loading-overlay')
};

// === API Functions ===
const api = {
    baseUrl: '',
    
    async analyzeText(text) {
        const response = await fetch(`${this.baseUrl}/analyze_text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        return response.json();
    },
    
    async analyzeImage(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.baseUrl}/analyze_image`, {
            method: 'POST',
            body: formData
        });
        return response.json();
    },
    
    async parseDemo(url) {
        const response = await fetch(`${this.baseUrl}/parse_demo`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        return response.json();
    },
    
    async getHistory() {
        const response = await fetch(`${this.baseUrl}/history`);
        return response.json();
    },
    
    async clearHistory() {
        const response = await fetch(`${this.baseUrl}/history`, {
            method: 'DELETE'
        });
        return response.json();
    }
};

// === UI Functions ===
const ui = {
    showLoading() {
        state.isLoading = true;
        elements.loadingOverlay.style.display = 'flex';
    },
    
    hideLoading() {
        state.isLoading = false;
        elements.loadingOverlay.style.display = 'none';
    },
    
    showTab(tabId) {
        state.currentTab = tabId;
        
        // Update navigation
        elements.navButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });
        
        // Update content
        elements.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === `${tabId}-tab`);
        });
        
        // Load history if needed
        if (tabId === 'history') {
            this.loadHistory();
        }
    },
    
    showResults(html) {
        elements.resultsContent.innerHTML = html;
        elements.resultsSection.hidden = false;
        elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    },
    
    hideResults() {
        elements.resultsSection.hidden = true;
    },
    
    showError(message) {
        const html = `
            <div class="error-message">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <span>${message}</span>
            </div>
        `;
        this.showResults(html);
    },
    
    renderTextAnalysis(analysis) {
        return `
            ${this.renderResultBlock('Сильные стороны', analysis.strengths, 'strengths')}
            ${this.renderResultBlock('Слабые стороны', analysis.weaknesses, 'weaknesses')}
            ${this.renderResultBlock('Уникальные предложения', analysis.unique_offers, 'unique')}
            ${this.renderResultBlock('Рекомендации', analysis.recommendations, 'recommendations')}
            ${analysis.summary ? `
                <div class="result-block result-summary">
                    <h3>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                        </svg>
                        Резюме
                    </h3>
                    <p>${analysis.summary}</p>
                </div>
            ` : ''}
        `;
    },
    
    renderImageAnalysis(analysis) {
        const scorePercent = (analysis.visual_style_score / 10) * 100;
        
        return `
            <div class="result-block">
                <h3>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5"/>
                        <polyline points="21 15 16 10 5 21"/>
                    </svg>
                    Описание изображения
                </h3>
                <p>${analysis.description}</p>
            </div>
            
            <div class="result-block">
                <h3>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                    Оценка визуального стиля
                </h3>
                <div class="score-display">
                    <span class="score-value">${analysis.visual_style_score}/10</span>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${scorePercent}%"></div>
                    </div>
                </div>
                <p>${analysis.visual_style_analysis}</p>
            </div>
            
            ${this.renderResultBlock('Маркетинговые инсайты', analysis.marketing_insights, 'insights')}
            ${this.renderResultBlock('Рекомендации', analysis.recommendations, 'recommendations')}
        `;
    },
    
    renderParsedContent(data) {
        const parsed = data;
        
        return `
            <div class="parsed-content">
                <div class="label">URL:</div>
                <div class="value">${parsed.url}</div>
                
                <div class="label">Title:</div>
                <div class="value">${parsed.title || 'Не найден'}</div>
                
                <div class="label">H1:</div>
                <div class="value">${parsed.h1 || 'Не найден'}</div>
                
                <div class="label">Первый абзац:</div>
                <div class="value">${parsed.first_paragraph || 'Не найден'}</div>
            </div>
            
            ${parsed.analysis ? this.renderTextAnalysis(parsed.analysis) : ''}
        `;
    },
    
    renderResultBlock(title, items, type) {
        if (!items || items.length === 0) return '';
        
        const icons = {
            strengths: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
            weaknesses: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
            unique: '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
            recommendations: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
            insights: '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>'
        };
        
        return `
            <div class="result-block">
                <h3>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        ${icons[type] || icons.recommendations}
                    </svg>
                    ${title}
                </h3>
                <ul>
                    ${items.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `;
    },
    
    async loadHistory() {
        try {
            const data = await api.getHistory();
            this.renderHistory(data.items);
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    },
    
    renderHistory(items) {
        if (!items || items.length === 0) {
            elements.historyList.innerHTML = `
                <div class="history-empty">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    <p>История пуста</p>
                </div>
            `;
            return;
        }
        
        const icons = {
            text: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
            image: '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
            parse: '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>'
        };
        
        const typeLabels = {
            text: 'Анализ текста',
            image: 'Анализ изображения',
            parse: 'Парсинг сайта'
        };
        
        elements.historyList.innerHTML = items.map(item => {
            const date = new Date(item.timestamp);
            const timeStr = date.toLocaleString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            return `
                <div class="history-item">
                    <div class="history-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            ${icons[item.request_type] || icons.text}
                        </svg>
                    </div>
                    <div class="history-content">
                        <div class="history-type">${typeLabels[item.request_type] || item.request_type}</div>
                        <div class="history-summary">${item.request_summary}</div>
                    </div>
                    <div class="history-time">${timeStr}</div>
                </div>
            `;
        }).join('');
    }
};

// === Event Handlers ===
const handlers = {
    // Navigation
    handleNavClick(e) {
        const btn = e.target.closest('.nav-btn');
        if (btn) {
            ui.showTab(btn.dataset.tab);
        }
    },
    
    // Text analysis
    async handleAnalyzeText() {
        const text = elements.competitorText.value.trim();
        
        if (text.length < 10) {
            ui.showError('Введите текст минимум 10 символов для анализа');
            return;
        }
        
        ui.showLoading();
        
        try {
            const result = await api.analyzeText(text);
            
            if (result.success && result.analysis) {
                ui.showResults(ui.renderTextAnalysis(result.analysis));
            } else {
                ui.showError(result.error || 'Произошла ошибка при анализе');
            }
        } catch (error) {
            ui.showError('Ошибка соединения с сервером');
            console.error(error);
        } finally {
            ui.hideLoading();
        }
    },
    
    // Image upload
    handleUploadClick() {
        elements.imageInput.click();
    },
    
    handleImageSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processImage(file);
        }
    },
    
    handleDragOver(e) {
        e.preventDefault();
        elements.uploadZone.classList.add('dragover');
    },
    
    handleDragLeave(e) {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');
    },
    
    handleDrop(e) {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');
        
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            this.processImage(file);
        }
    },
    
    processImage(file) {
        state.selectedImage = file;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            elements.imagePreview.src = e.target.result;
            elements.previewContainer.hidden = false;
            elements.uploadZone.querySelector('.upload-content').hidden = true;
            elements.analyzeImageBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    },
    
    handleRemoveImage() {
        state.selectedImage = null;
        elements.imageInput.value = '';
        elements.imagePreview.src = '';
        elements.previewContainer.hidden = true;
        elements.uploadZone.querySelector('.upload-content').hidden = false;
        elements.analyzeImageBtn.disabled = true;
    },
    
    async handleAnalyzeImage() {
        if (!state.selectedImage) {
            ui.showError('Выберите изображение для анализа');
            return;
        }
        
        ui.showLoading();
        
        try {
            const result = await api.analyzeImage(state.selectedImage);
            
            if (result.success && result.analysis) {
                ui.showResults(ui.renderImageAnalysis(result.analysis));
            } else {
                ui.showError(result.error || 'Произошла ошибка при анализе изображения');
            }
        } catch (error) {
            ui.showError('Ошибка соединения с сервером');
            console.error(error);
        } finally {
            ui.hideLoading();
        }
    },
    
    // Parse demo
    async handleParse() {
        let url = elements.urlInput.value.trim();
        
        if (!url) {
            ui.showError('Введите URL сайта для парсинга');
            return;
        }
        
        // Add protocol if missing
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            url = 'https://' + url;
        }
        
        ui.showLoading();
        
        try {
            const result = await api.parseDemo(url);
            
            if (result.success && result.data) {
                ui.showResults(ui.renderParsedContent(result.data));
            } else {
                ui.showError(result.error || 'Не удалось распарсить сайт');
            }
        } catch (error) {
            ui.showError('Ошибка соединения с сервером');
            console.error(error);
        } finally {
            ui.hideLoading();
        }
    },
    
    // History
    async handleClearHistory() {
        if (!confirm('Вы уверены, что хотите очистить историю?')) {
            return;
        }
        
        try {
            await api.clearHistory();
            ui.renderHistory([]);
        } catch (error) {
            console.error('Failed to clear history:', error);
        }
    },
    
    // Results
    handleCloseResults() {
        ui.hideResults();
    }
};

// === Initialize ===
function init() {
    // Navigation
    elements.navButtons.forEach(btn => {
        btn.addEventListener('click', handlers.handleNavClick.bind(handlers));
    });
    
    // Text analysis
    elements.analyzeTextBtn.addEventListener('click', handlers.handleAnalyzeText.bind(handlers));
    
    // Image upload
    elements.uploadZone.addEventListener('click', handlers.handleUploadClick.bind(handlers));
    elements.imageInput.addEventListener('change', handlers.handleImageSelect.bind(handlers));
    elements.uploadZone.addEventListener('dragover', handlers.handleDragOver.bind(handlers));
    elements.uploadZone.addEventListener('dragleave', handlers.handleDragLeave.bind(handlers));
    elements.uploadZone.addEventListener('drop', handlers.handleDrop.bind(handlers));
    elements.removeImageBtn.addEventListener('click', handlers.handleRemoveImage.bind(handlers));
    elements.analyzeImageBtn.addEventListener('click', handlers.handleAnalyzeImage.bind(handlers));
    
    // Parse demo
    elements.parseBtn.addEventListener('click', handlers.handleParse.bind(handlers));
    elements.urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handlers.handleParse.call(handlers);
    });
    
    // History
    elements.clearHistoryBtn.addEventListener('click', handlers.handleClearHistory.bind(handlers));
    
    // Results
    elements.closeResultsBtn.addEventListener('click', handlers.handleCloseResults.bind(handlers));
    
    // Show default tab
    ui.showTab('text');
}

// Start app
document.addEventListener('DOMContentLoaded', init);


```

Теперь запустите сервер снова и обновите страницу:

Исправил! Теперь loading overlay использует `style="display: none;"` вместо атрибута `hidden`. 

Запустите сервер:
```powershell
python run.py
```

Затем обновите страницу в браузере (Ctrl+F5).

```powershell
python run.py
```

---

**User**

Перепиши блок парсинга, он должен запускать chrome открывать страницу -> и страницу будет анализировать ИИ

---

**Cursor**

Перепишу парсинг с использованием браузера Chrome через Playwright. Он будет делать скриншот страницы и отправлять на анализ ИИ.

```pip-requirements
fastapi>=0.104.0
uvicorn>=0.24.0
openai>=1.6.0
httpx>=0.25.0
python-multipart>=0.0.6
beautifulsoup4>=4.12.0
lxml>=5.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
aiofiles>=23.2.0
Pillow>=10.0.0
playwright>=1.40.0


```

```python
"""
Сервис для парсинга веб-страниц через браузер Chrome
"""
import base64
import asyncio
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Browser, Page

from backend.config import settings


class ParserService:
    """Парсинг веб-страниц через Chrome с созданием скриншота"""
    
    def __init__(self):
        self.timeout = settings.parser_timeout * 1000  # В миллисекундах
        self._browser: Optional[Browser] = None
        self._playwright = None
    
    async def _get_browser(self) -> Browser:
        """Получить или создать экземпляр браузера"""
        if self._browser is None or not self._browser.is_connected():
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,  # Без GUI
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
        return self._browser
    
    async def close(self):
        """Закрыть браузер"""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
    
    async def parse_url(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[bytes], Optional[str]]:
        """
        Открывает URL в Chrome, извлекает данные и делает скриншот
        
        Returns:
            Tuple[title, h1, first_paragraph, screenshot_bytes, error]
        """
        # Добавляем протокол если его нет
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        page: Optional[Page] = None
        
        try:
            browser = await self._get_browser()
            page = await browser.new_page(
                viewport={'width': 1920, 'height': 1080},
                user_agent=settings.parser_user_agent
            )
            
            # Переходим на страницу
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            
            # Ждём немного для полной загрузки динамического контента
            await asyncio.sleep(1)
            
            # Извлекаем title
            title = await page.title()
            
            # Извлекаем h1
            h1 = None
            h1_element = await page.query_selector('h1')
            if h1_element:
                h1 = await h1_element.inner_text()
                h1 = h1.strip() if h1 else None
            
            # Извлекаем первый абзац
            first_paragraph = None
            paragraphs = await page.query_selector_all('p')
            for p in paragraphs:
                text = await p.inner_text()
                text = text.strip() if text else ""
                if len(text) > 50:
                    first_paragraph = text[:500]
                    break
            
            # Делаем скриншот всей видимой области
            screenshot_bytes = await page.screenshot(
                type='jpeg',
                quality=85,
                full_page=False  # Только видимая область
            )
            
            return title, h1, first_paragraph, screenshot_bytes, None
            
        except Exception as e:
            error_msg = str(e)
            if 'Timeout' in error_msg:
                return None, None, None, None, "Превышено время ожидания загрузки страницы"
            elif 'net::ERR_NAME_NOT_RESOLVED' in error_msg:
                return None, None, None, None, "Не удалось найти сайт по указанному адресу"
            elif 'net::ERR_CONNECTION_REFUSED' in error_msg:
                return None, None, None, None, "Соединение отклонено сервером"
            else:
                return None, None, None, None, f"Ошибка при загрузке страницы: {error_msg[:200]}"
        finally:
            if page:
                await page.close()
    
    def screenshot_to_base64(self, screenshot_bytes: bytes) -> str:
        """Конвертировать скриншот в base64"""
        return base64.b64encode(screenshot_bytes).decode('utf-8')


# Глобальный экземпляр
parser_service = ParserService()

```

```python
"""
Сервис для работы с OpenAI API
"""
import base64
import json
import re
from typing import Optional

from openai import OpenAI

from backend.config import settings
from backend.models.schemas import CompetitorAnalysis, ImageAnalysis


class OpenAIService:
    """Сервис для анализа через OpenAI"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.vision_model = settings.openai_vision_model
    
    def _parse_json_response(self, content: str) -> dict:
        """Извлечь JSON из ответа модели"""
        # Пробуем найти JSON в markdown блоке
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)
        
        # Пробуем найти JSON объект
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}
    
    async def analyze_text(self, text: str) -> CompetitorAnalysis:
        """Анализ текста конкурента"""
        system_prompt = """Ты — эксперт по конкурентному анализу. Проанализируй предоставленный текст конкурента и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
    "weaknesses": ["слабая сторона 1", "слабая сторона 2", ...],
    "unique_offers": ["уникальное предложение 1", "уникальное предложение 2", ...],
    "recommendations": ["рекомендация 1", "рекомендация 2", ...],
    "summary": "Краткое резюме анализа"
}

Важно:
- Каждый массив должен содержать 3-5 пунктов
- Пиши на русском языке
- Будь конкретен и практичен в рекомендациях"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Проанализируй текст конкурента:\n\n{text}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        data = self._parse_json_response(content)
        
        return CompetitorAnalysis(
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            unique_offers=data.get("unique_offers", []),
            recommendations=data.get("recommendations", []),
            summary=data.get("summary", "")
        )
    
    async def analyze_image(self, image_base64: str, mime_type: str = "image/jpeg") -> ImageAnalysis:
        """Анализ изображения (баннер, сайт, упаковка)"""
        system_prompt = """Ты — эксперт по визуальному маркетингу и дизайну. Проанализируй изображение конкурента (баннер, сайт, упаковка товара и т.д.) и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "description": "Детальное описание того, что изображено",
    "marketing_insights": ["инсайт 1", "инсайт 2", ...],
    "visual_style_score": 7,
    "visual_style_analysis": "Анализ визуального стиля конкурента",
    "recommendations": ["рекомендация 1", "рекомендация 2", ...]
}

Важно:
- visual_style_score от 0 до 10
- Каждый массив должен содержать 3-5 пунктов
- Пиши на русском языке
- Оценивай: цветовую палитру, типографику, композицию, UX/UI элементы"""

        response = self.client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Проанализируй это изображение конкурента с точки зрения маркетинга и дизайна:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        data = self._parse_json_response(content)
        
        return ImageAnalysis(
            description=data.get("description", ""),
            marketing_insights=data.get("marketing_insights", []),
            visual_style_score=data.get("visual_style_score", 5),
            visual_style_analysis=data.get("visual_style_analysis", ""),
            recommendations=data.get("recommendations", [])
        )
    
    async def analyze_parsed_content(
        self, 
        title: Optional[str], 
        h1: Optional[str], 
        paragraph: Optional[str]
    ) -> CompetitorAnalysis:
        """Анализ распарсенного контента сайта"""
        content_parts = []
        if title:
            content_parts.append(f"Заголовок страницы (title): {title}")
        if h1:
            content_parts.append(f"Главный заголовок (H1): {h1}")
        if paragraph:
            content_parts.append(f"Первый абзац: {paragraph}")
        
        combined_text = "\n\n".join(content_parts)
        
        if not combined_text.strip():
            return CompetitorAnalysis(
                summary="Не удалось извлечь контент для анализа"
            )
        
        return await self.analyze_text(combined_text)
    
    async def analyze_website_screenshot(
        self,
        screenshot_base64: str,
        url: str,
        title: Optional[str] = None,
        h1: Optional[str] = None,
        first_paragraph: Optional[str] = None
    ) -> CompetitorAnalysis:
        """Комплексный анализ сайта конкурента по скриншоту"""
        
        # Формируем контекст из извлечённых данных
        context_parts = [f"URL сайта: {url}"]
        if title:
            context_parts.append(f"Title страницы: {title}")
        if h1:
            context_parts.append(f"Главный заголовок (H1): {h1}")
        if first_paragraph:
            context_parts.append(f"Текст на странице: {first_paragraph[:300]}")
        
        context = "\n".join(context_parts)
        
        system_prompt = """Ты — эксперт по конкурентному анализу и UX/UI дизайну. Проанализируй скриншот сайта конкурента и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
    "weaknesses": ["слабая сторона 1", "слабая сторона 2", ...],
    "unique_offers": ["уникальное предложение/фича 1", "уникальное предложение/фича 2", ...],
    "recommendations": ["рекомендация 1", "рекомендация 2", ...],
    "summary": "Комплексное резюме анализа сайта конкурента"
}

При анализе обращай внимание на:
- Дизайн и визуальный стиль (цвета, шрифты, композиция)
- UX/UI: навигация, расположение элементов, CTA кнопки
- Контент: заголовки, тексты, призывы к действию
- Уникальные торговые предложения (УТП)
- Целевая аудитория (на кого ориентирован сайт)
- Технологичность и современность дизайна

Важно:
- Каждый массив должен содержать 4-6 конкретных пунктов
- Пиши на русском языке
- Будь конкретен и практичен
- Давай actionable рекомендации"""

        response = self.client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Проведи комплексный конкурентный анализ этого сайта:\n\n{context}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{screenshot_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        content = response.choices[0].message.content
        data = self._parse_json_response(content)
        
        return CompetitorAnalysis(
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            unique_offers=data.get("unique_offers", []),
            recommendations=data.get("recommendations", []),
            summary=data.get("summary", "")
        )


# Глобальный экземпляр
openai_service = OpenAIService()


```

Теперь обновлю эндпоинт `/parse_demo` в main.py:

```python
"""
Главный модуль FastAPI приложения
Мониторинг конкурентов - MVP ассистент
"""
import base64
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from backend.config import settings
from backend.models.schemas import (
    TextAnalysisRequest,
    TextAnalysisResponse,
    ImageAnalysisResponse,
    ParseDemoRequest,
    ParseDemoResponse,
    ParsedContent,
    HistoryResponse
)
from backend.services.openai_service import openai_service
from backend.services.parser_service import parser_service
from backend.services.history_service import history_service


# Инициализация приложения
app = FastAPI(
    title="Мониторинг конкурентов",
    description="MVP ассистент для анализа конкурентов с поддержкой текста и изображений",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Эндпоинты ===

@app.get("/")
async def root():
    """Главная страница - отдаём фронтенд"""
    return FileResponse("frontend/index.html")


@app.post("/analyze_text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Анализ текста конкурента
    
    Принимает текст и возвращает структурированную аналитику:
    - Сильные стороны
    - Слабые стороны
    - Уникальные предложения
    - Рекомендации по улучшению стратегии
    """
    try:
        analysis = await openai_service.analyze_text(request.text)
        
        # Сохраняем в историю
        history_service.add_entry(
            request_type="text",
            request_summary=request.text[:100] + "..." if len(request.text) > 100 else request.text,
            response_summary=analysis.summary
        )
        
        return TextAnalysisResponse(
            success=True,
            analysis=analysis
        )
    except Exception as e:
        return TextAnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/analyze_image", response_model=ImageAnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    Анализ изображения конкурента
    
    Принимает изображение (баннер, сайт, упаковка) и возвращает:
    - Описание изображения
    - Маркетинговые инсайты
    - Оценку визуального стиля
    - Рекомендации
    """
    # Проверяем тип файла
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(allowed_types)}"
        )
    
    try:
        # Читаем и кодируем изображение
        content = await file.read()
        image_base64 = base64.b64encode(content).decode('utf-8')
        
        # Анализируем
        analysis = await openai_service.analyze_image(
            image_base64=image_base64,
            mime_type=file.content_type
        )
        
        # Сохраняем в историю
        history_service.add_entry(
            request_type="image",
            request_summary=f"Изображение: {file.filename}",
            response_summary=analysis.description[:200] if analysis.description else "Анализ изображения"
        )
        
        return ImageAnalysisResponse(
            success=True,
            analysis=analysis
        )
    except Exception as e:
        return ImageAnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/parse_demo", response_model=ParseDemoResponse)
async def parse_demo(request: ParseDemoRequest):
    """
    Парсинг и анализ сайта конкурента через Chrome
    
    Открывает URL в браузере Chrome, извлекает:
    - Title страницы
    - H1 заголовок
    - Первый абзац
    - Скриншот страницы
    
    И передаёт скриншот + данные на анализ ИИ
    """
    try:
        # Открываем страницу в Chrome и делаем скриншот
        title, h1, first_paragraph, screenshot_bytes, error = await parser_service.parse_url(request.url)
        
        if error:
            return ParseDemoResponse(
                success=False,
                error=error
            )
        
        # Конвертируем скриншот в base64
        screenshot_base64 = parser_service.screenshot_to_base64(screenshot_bytes) if screenshot_bytes else None
        
        # Анализируем сайт через Vision API (скриншот + контекст)
        if screenshot_base64:
            analysis = await openai_service.analyze_website_screenshot(
                screenshot_base64=screenshot_base64,
                url=request.url,
                title=title,
                h1=h1,
                first_paragraph=first_paragraph
            )
        else:
            # Fallback на текстовый анализ если скриншот не получился
            analysis = await openai_service.analyze_parsed_content(
                title=title,
                h1=h1,
                paragraph=first_paragraph
            )
        
        parsed_content = ParsedContent(
            url=request.url,
            title=title,
            h1=h1,
            first_paragraph=first_paragraph,
            analysis=analysis
        )
        
        # Сохраняем в историю
        history_service.add_entry(
            request_type="parse",
            request_summary=f"URL: {request.url}",
            response_summary=analysis.summary[:100] if analysis.summary else f"Title: {title or 'N/A'}"
        )
        
        return ParseDemoResponse(
            success=True,
            data=parsed_content
        )
    except Exception as e:
        return ParseDemoResponse(
            success=False,
            error=str(e)
        )


@app.get("/history", response_model=HistoryResponse)
async def get_history():
    """
    Получить историю последних 10 запросов
    """
    items = history_service.get_history()
    return HistoryResponse(
        items=items,
        total=len(items)
    )


@app.delete("/history")
async def clear_history():
    """
    Очистить историю запросов
    """
    history_service.clear_history()
    return {"success": True, "message": "История очищена"}


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {
        "status": "healthy",
        "service": "Competitor Monitor",
        "version": "1.0.0"
    }


# Статические файлы для фронтенда
app.mount("/static", StaticFiles(directory="frontend"), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )


```

Добавлю обработчик закрытия браузера при остановке сервера:

```python
"""
Главный модуль FastAPI приложения
Мониторинг конкурентов - MVP ассистент
"""
import base64
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from backend.config import settings
from backend.models.schemas import (
    TextAnalysisRequest,
    TextAnalysisResponse,
    ImageAnalysisResponse,
    ParseDemoRequest,
    ParseDemoResponse,
    ParsedContent,
    HistoryResponse
)
from backend.services.openai_service import openai_service
from backend.services.parser_service import parser_service
from backend.services.history_service import history_service


# Инициализация приложения
app = FastAPI(
    title="Мониторинг конкурентов",
    description="MVP ассистент для анализа конкурентов с поддержкой текста и изображений",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Эндпоинты ===

@app.get("/")
async def root():
    """Главная страница - отдаём фронтенд"""
    return FileResponse("frontend/index.html")


@app.post("/analyze_text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Анализ текста конкурента
    
    Принимает текст и возвращает структурированную аналитику:
    - Сильные стороны
    - Слабые стороны
    - Уникальные предложения
    - Рекомендации по улучшению стратегии
    """
    try:
        analysis = await openai_service.analyze_text(request.text)
        
        # Сохраняем в историю
        history_service.add_entry(
            request_type="text",
            request_summary=request.text[:100] + "..." if len(request.text) > 100 else request.text,
            response_summary=analysis.summary
        )
        
        return TextAnalysisResponse(
            success=True,
            analysis=analysis
        )
    except Exception as e:
        return TextAnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/analyze_image", response_model=ImageAnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    Анализ изображения конкурента
    
    Принимает изображение (баннер, сайт, упаковка) и возвращает:
    - Описание изображения
    - Маркетинговые инсайты
    - Оценку визуального стиля
    - Рекомендации
    """
    # Проверяем тип файла
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(allowed_types)}"
        )
    
    try:
        # Читаем и кодируем изображение
        content = await file.read()
        image_base64 = base64.b64encode(content).decode('utf-8')
        
        # Анализируем
        analysis = await openai_service.analyze_image(
            image_base64=image_base64,
            mime_type=file.content_type
        )
        
        # Сохраняем в историю
        history_service.add_entry(
            request_type="image",
            request_summary=f"Изображение: {file.filename}",
            response_summary=analysis.description[:200] if analysis.description else "Анализ изображения"
        )
        
        return ImageAnalysisResponse(
            success=True,
            analysis=analysis
        )
    except Exception as e:
        return ImageAnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/parse_demo", response_model=ParseDemoResponse)
async def parse_demo(request: ParseDemoRequest):
    """
    Парсинг и анализ сайта конкурента через Chrome
    
    Открывает URL в браузере Chrome, извлекает:
    - Title страницы
    - H1 заголовок
    - Первый абзац
    - Скриншот страницы
    
    И передаёт скриншот + данные на анализ ИИ
    """
    try:
        # Открываем страницу в Chrome и делаем скриншот
        title, h1, first_paragraph, screenshot_bytes, error = await parser_service.parse_url(request.url)
        
        if error:
            return ParseDemoResponse(
                success=False,
                error=error
            )
        
        # Конвертируем скриншот в base64
        screenshot_base64 = parser_service.screenshot_to_base64(screenshot_bytes) if screenshot_bytes else None
        
        # Анализируем сайт через Vision API (скриншот + контекст)
        if screenshot_base64:
            analysis = await openai_service.analyze_website_screenshot(
                screenshot_base64=screenshot_base64,
                url=request.url,
                title=title,
                h1=h1,
                first_paragraph=first_paragraph
            )
        else:
            # Fallback на текстовый анализ если скриншот не получился
            analysis = await openai_service.analyze_parsed_content(
                title=title,
                h1=h1,
                paragraph=first_paragraph
            )
        
        parsed_content = ParsedContent(
            url=request.url,
            title=title,
            h1=h1,
            first_paragraph=first_paragraph,
            analysis=analysis
        )
        
        # Сохраняем в историю
        history_service.add_entry(
            request_type="parse",
            request_summary=f"URL: {request.url}",
            response_summary=analysis.summary[:100] if analysis.summary else f"Title: {title or 'N/A'}"
        )
        
        return ParseDemoResponse(
            success=True,
            data=parsed_content
        )
    except Exception as e:
        return ParseDemoResponse(
            success=False,
            error=str(e)
        )


@app.get("/history", response_model=HistoryResponse)
async def get_history():
    """
    Получить историю последних 10 запросов
    """
    items = history_service.get_history()
    return HistoryResponse(
        items=items,
        total=len(items)
    )


@app.delete("/history")
async def clear_history():
    """
    Очистить историю запросов
    """
    history_service.clear_history()
    return {"success": True, "message": "История очищена"}


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {
        "status": "healthy",
        "service": "Competitor Monitor",
        "version": "1.0.0"
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Закрытие браузера при остановке сервера"""
    await parser_service.close()


# Статические файлы для фронтенда
app.mount("/static", StaticFiles(directory="frontend"), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )


```

Теперь нужно установить Playwright и скачать браузер Chrome. Выполните команды:

Готово! Блок парсинга переписан. Теперь он:

1. **Открывает Chrome** (headless режим) через Playwright
2. **Загружает страницу** и ждёт полной загрузки
3. **Делает скриншот** видимой области (1920x1080)
4. **Извлекает данные**: title, h1, первый абзац
5. **Отправляет скриншот на анализ ИИ** (GPT-4 Vision)

## Установка

Выполните эти команды:

```powershell
# Установить Playwright
pip install playwright

# Скачать браузер Chromium
playwright install chromium
```

Затем перезапустите сервер:

```powershell
python run.py
```

Теперь при парсинге сайта ИИ будет видеть реальный скриншот страницы и давать более точный анализ дизайна, UX/UI и контента!

```powershell
# Установить Playwright
pip install playwright

# Скачать браузер Chromium
playwright install chromium
```

```powershell
python run.py
```

---

**User**

Используй selenium для парсинга

---

**Cursor**

Перепишу парсинг на Selenium:

```pip-requirements
fastapi>=0.104.0
uvicorn>=0.24.0
openai>=1.6.0
httpx>=0.25.0
python-multipart>=0.0.6
beautifulsoup4>=4.12.0
lxml>=5.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
aiofiles>=23.2.0
Pillow>=10.0.0
selenium>=4.15.0
webdriver-manager>=4.0.0


```

```python
"""
Сервис для парсинга веб-страниц через Selenium Chrome
"""
import base64
import asyncio
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from backend.config import settings


class ParserService:
    """Парсинг веб-страниц через Chrome с созданием скриншота"""
    
    def __init__(self):
        self.timeout = settings.parser_timeout
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def _create_driver(self) -> webdriver.Chrome:
        """Создать новый экземпляр Chrome драйвера"""
        options = Options()
        options.add_argument('--headless=new')  # Новый headless режим
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'--user-agent={settings.parser_user_agent}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Автоматическая установка ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        return driver
    
    def _parse_sync(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[bytes], Optional[str]]:
        """
        Синхронный парсинг URL (выполняется в отдельном потоке)
        
        Returns:
            Tuple[title, h1, first_paragraph, screenshot_bytes, error]
        """
        driver = None
        
        try:
            driver = self._create_driver()
            driver.set_page_load_timeout(self.timeout)
            
            # Переходим на страницу
            driver.get(url)
            
            # Ждём загрузки body
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Даём странице время на загрузку динамического контента
            import time
            time.sleep(2)
            
            # Извлекаем title
            title = driver.title
            
            # Извлекаем h1
            h1 = None
            try:
                h1_element = driver.find_element(By.TAG_NAME, 'h1')
                h1 = h1_element.text.strip() if h1_element.text else None
            except:
                pass
            
            # Извлекаем первый абзац
            first_paragraph = None
            try:
                paragraphs = driver.find_elements(By.TAG_NAME, 'p')
                for p in paragraphs:
                    text = p.text.strip() if p.text else ""
                    if len(text) > 50:
                        first_paragraph = text[:500]
                        break
            except:
                pass
            
            # Делаем скриншот
            screenshot_bytes = driver.get_screenshot_as_png()
            
            return title, h1, first_paragraph, screenshot_bytes, None
            
        except TimeoutException:
            return None, None, None, None, "Превышено время ожидания загрузки страницы"
        except WebDriverException as e:
            error_msg = str(e)
            if 'net::ERR_NAME_NOT_RESOLVED' in error_msg:
                return None, None, None, None, "Не удалось найти сайт по указанному адресу"
            elif 'net::ERR_CONNECTION_REFUSED' in error_msg:
                return None, None, None, None, "Соединение отклонено сервером"
            elif 'net::ERR_CONNECTION_TIMED_OUT' in error_msg:
                return None, None, None, None, "Превышено время ожидания соединения"
            else:
                return None, None, None, None, f"Ошибка браузера: {error_msg[:200]}"
        except Exception as e:
            return None, None, None, None, f"Ошибка при загрузке страницы: {str(e)[:200]}"
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    async def parse_url(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[bytes], Optional[str]]:
        """
        Асинхронный парсинг URL через Chrome
        
        Returns:
            Tuple[title, h1, first_paragraph, screenshot_bytes, error]
        """
        # Добавляем протокол если его нет
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Запускаем синхронный парсинг в отдельном потоке
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor,
            self._parse_sync,
            url
        )
        
        return result
    
    def screenshot_to_base64(self, screenshot_bytes: bytes) -> str:
        """Конвертировать скриншот в base64"""
        return base64.b64encode(screenshot_bytes).decode('utf-8')
    
    async def close(self):
        """Закрыть executor"""
        self._executor.shutdown(wait=False)


# Глобальный экземпляр
parser_service = ParserService()

```

Готово! Парсинг переписан на Selenium. Установите зависимости:

```powershell
pip install selenium webdriver-manager
```

ChromeDriver скачается автоматически при первом запуске.

Затем перезапустите сервер:

```powershell
python run.py
```

**Что делает парсер:**
1. Открывает Chrome в headless режиме
2. Загружает страницу и ждёт 2 сек для динамического контента
3. Извлекает title, h1, первый абзац
4. Делает скриншот (1920x1080)
5. Отправляет скриншот на анализ GPT-4 Vision
6. Закрывает браузер

```powershell
pip install selenium webdriver-manager
```

```powershell
python run.py
```

---

**User**

Перенеси проект с openai на proxy_api(в env ключ PROXY_API_KEY)



https://proxyapi.ru/docs/openai-text-generation 

Вот документация

---

**Cursor**

Перенесу проект на ProxyAPI. Нужно обновить конфиг и сервис OpenAI:

```python
"""
Конфигурация приложения
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


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
    
    # Парсер
    parser_timeout: int = 10
    parser_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


```

```python
"""
Сервис для работы с ProxyAPI (OpenAI-совместимый API)
https://proxyapi.ru/docs/openai-text-generation
"""
import base64
import json
import re
from typing import Optional

from openai import OpenAI

from backend.config import settings
from backend.models.schemas import CompetitorAnalysis, ImageAnalysis


class OpenAIService:
    """Сервис для анализа через ProxyAPI"""
    
    def __init__(self):
        # ProxyAPI - OpenAI-совместимый API для России
        self.client = OpenAI(
            api_key=settings.proxy_api_key,
            base_url=settings.proxy_api_base_url
        )
        self.model = settings.openai_model
        self.vision_model = settings.openai_vision_model
    
    def _parse_json_response(self, content: str) -> dict:
        """Извлечь JSON из ответа модели"""
        # Пробуем найти JSON в markdown блоке
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)
        
        # Пробуем найти JSON объект
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}
    
    async def analyze_text(self, text: str) -> CompetitorAnalysis:
        """Анализ текста конкурента"""
        system_prompt = """Ты — эксперт по конкурентному анализу. Проанализируй предоставленный текст конкурента и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
    "weaknesses": ["слабая сторона 1", "слабая сторона 2", ...],
    "unique_offers": ["уникальное предложение 1", "уникальное предложение 2", ...],
    "recommendations": ["рекомендация 1", "рекомендация 2", ...],
    "summary": "Краткое резюме анализа"
}

Важно:
- Каждый массив должен содержать 3-5 пунктов
- Пиши на русском языке
- Будь конкретен и практичен в рекомендациях"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Проанализируй текст конкурента:\n\n{text}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        data = self._parse_json_response(content)
        
        return CompetitorAnalysis(
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            unique_offers=data.get("unique_offers", []),
            recommendations=data.get("recommendations", []),
            summary=data.get("summary", "")
        )
    
    async def analyze_image(self, image_base64: str, mime_type: str = "image/jpeg") -> ImageAnalysis:
        """Анализ изображения (баннер, сайт, упаковка)"""
        system_prompt = """Ты — эксперт по визуальному маркетингу и дизайну. Проанализируй изображение конкурента (баннер, сайт, упаковка товара и т.д.) и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "description": "Детальное описание того, что изображено",
    "marketing_insights": ["инсайт 1", "инсайт 2", ...],
    "visual_style_score": 7,
    "visual_style_analysis": "Анализ визуального стиля конкурента",
    "recommendations": ["рекомендация 1", "рекомендация 2", ...]
}

Важно:
- visual_style_score от 0 до 10
- Каждый массив должен содержать 3-5 пунктов
- Пиши на русском языке
- Оценивай: цветовую палитру, типографику, композицию, UX/UI элементы"""

        response = self.client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Проанализируй это изображение конкурента с точки зрения маркетинга и дизайна:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        data = self._parse_json_response(content)
        
        return ImageAnalysis(
            description=data.get("description", ""),
            marketing_insights=data.get("marketing_insights", []),
            visual_style_score=data.get("visual_style_score", 5),
            visual_style_analysis=data.get("visual_style_analysis", ""),
            recommendations=data.get("recommendations", [])
        )
    
    async def analyze_parsed_content(
        self, 
        title: Optional[str], 
        h1: Optional[str], 
        paragraph: Optional[str]
    ) -> CompetitorAnalysis:
        """Анализ распарсенного контента сайта"""
        content_parts = []
        if title:
            content_parts.append(f"Заголовок страницы (title): {title}")
        if h1:
            content_parts.append(f"Главный заголовок (H1): {h1}")
        if paragraph:
            content_parts.append(f"Первый абзац: {paragraph}")
        
        combined_text = "\n\n".join(content_parts)
        
        if not combined_text.strip():
            return CompetitorAnalysis(
                summary="Не удалось извлечь контент для анализа"
            )
        
        return await self.analyze_text(combined_text)
    
    async def analyze_website_screenshot(
        self,
        screenshot_base64: str,
        url: str,
        title: Optional[str] = None,
        h1: Optional[str] = None,
        first_paragraph: Optional[str] = None
    ) -> CompetitorAnalysis:
        """Комплексный анализ сайта конкурента по скриншоту"""
        
        # Формируем контекст из извлечённых данных
        context_parts = [f"URL сайта: {url}"]
        if title:
            context_parts.append(f"Title страницы: {title}")
        if h1:
            context_parts.append(f"Главный заголовок (H1): {h1}")
        if first_paragraph:
            context_parts.append(f"Текст на странице: {first_paragraph[:300]}")
        
        context = "\n".join(context_parts)
        
        system_prompt = """Ты — эксперт по конкурентному анализу и UX/UI дизайну. Проанализируй скриншот сайта конкурента и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
    "weaknesses": ["слабая сторона 1", "слабая сторона 2", ...],
    "unique_offers": ["уникальное предложение/фича 1", "уникальное предложение/фича 2", ...],
    "recommendations": ["рекомендация 1", "рекомендация 2", ...],
    "summary": "Комплексное резюме анализа сайта конкурента"
}

При анализе обращай внимание на:
- Дизайн и визуальный стиль (цвета, шрифты, композиция)
- UX/UI: навигация, расположение элементов, CTA кнопки
- Контент: заголовки, тексты, призывы к действию
- Уникальные торговые предложения (УТП)
- Целевая аудитория (на кого ориентирован сайт)
- Технологичность и современность дизайна

Важно:
- Каждый массив должен содержать 4-6 конкретных пунктов
- Пиши на русском языке
- Будь конкретен и практичен
- Давай actionable рекомендации"""

        response = self.client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Проведи комплексный конкурентный анализ этого сайта:\n\n{context}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{screenshot_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        content = response.choices[0].message.content
        data = self._parse_json_response(content)
        
        return CompetitorAnalysis(
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            unique_offers=data.get("unique_offers", []),
            recommendations=data.get("recommendations", []),
            summary=data.get("summary", "")
        )


# Глобальный экземпляр
openai_service = OpenAIService()


```

```plaintext
# ProxyAPI Configuration
# Получить ключ: https://proxyapi.ru/
# Документация: https://proxyapi.ru/docs/openai-text-generation

PROXY_API_KEY=your_proxy_api_key_here

# Модели (опционально, по умолчанию gpt-4o-mini)
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o-mini

# Доступные модели ProxyAPI:
# - gpt-4o (лучшее качество)
# - gpt-4o-mini (баланс цена/качество)
# - gpt-4-turbo
# - gpt-3.5-turbo

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

```

```markdown
# 📚 Документация API - Мониторинг конкурентов

## Содержание

1. [Структура проекта](#структура-проекта)
2. [Описание API](#описание-api)
3. [Примеры запросов](#примеры-запросов)
4. [Мультимодальные функции](#мультимодальные-функции)
5. [Модели данных](#модели-данных)

---

## Структура проекта

```
competitor-monitor/
│
├── backend/                     # Backend модуль
│   ├── __init__.py
│   ├── main.py                  # Главный файл FastAPI
│   ├── config.py                # Конфигурация приложения
│   │
│   ├── models/                  # Pydantic модели
│   │   ├── __init__.py
│   │   └── schemas.py           # Схемы запросов/ответов
│   │
│   └── services/                # Бизнес-логика
│       ├── __init__.py
│       ├── openai_service.py    # Интеграция с OpenAI
│       ├── parser_service.py    # Парсинг веб-страниц
│       └── history_service.py   # Управление историей
│
├── frontend/                    # Frontend модуль
│   ├── index.html               # Главная HTML страница
│   ├── styles.css               # CSS стили
│   └── app.js                   # JavaScript приложение
│
├── requirements.txt             # Python зависимости
├── env.example.txt              # Пример переменных окружения
├── history.json                 # Файл истории запросов
├── README.md                    # Описание проекта
└── docs.md                      # Эта документация
```

---

## Описание API

### Базовый URL

```
http://localhost:8000
```

### Эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Главная страница (веб-интерфейс) |
| POST | `/analyze_text` | Анализ текста конкурента |
| POST | `/analyze_image` | Анализ изображения конкурента |
| POST | `/parse_demo` | Парсинг и анализ сайта по URL |
| GET | `/history` | Получение истории запросов |
| DELETE | `/history` | Очистка истории запросов |
| GET | `/health` | Проверка работоспособности |
| GET | `/docs` | Swagger UI документация |
| GET | `/redoc` | ReDoc документация |

---

## Примеры запросов

### 1. Анализ текста (`POST /analyze_text`)

**Запрос:**
```bash
curl -X POST "http://localhost:8000/analyze_text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Наша компания предлагает уникальные решения для бизнеса. Мы работаем на рынке 10 лет и обслуживаем более 1000 клиентов. Наши преимущества: быстрая доставка, гарантия качества, индивидуальный подход к каждому клиенту."
  }'
```

**Ответ:**
```json
{
  "success": true,
  "analysis": {
    "strengths": [
      "Долгий опыт работы на рынке (10 лет)",
      "Большая клиентская база (1000+ клиентов)",
      "Комплексный подход к обслуживанию"
    ],
    "weaknesses": [
      "Отсутствие конкретных цен",
      "Нет упоминания о технологиях",
      "Общие формулировки без специфики"
    ],
    "unique_offers": [
      "Индивидуальный подход к каждому клиенту",
      "Гарантия качества"
    ],
    "recommendations": [
      "Добавить конкретные цифры и кейсы",
      "Указать уникальные технологические преимущества",
      "Включить отзывы клиентов"
    ],
    "summary": "Компания позиционирует себя как надёжного партнёра с опытом, но маркетинговые материалы требуют конкретизации для повышения конверсии."
  },
  "error": null
}
```

### 2. Анализ изображения (`POST /analyze_image`)

**Запрос:**
```bash
curl -X POST "http://localhost:8000/analyze_image" \
  -F "file=@banner.jpg"
```

**Ответ:**
```json
{
  "success": true,
  "analysis": {
    "description": "Рекламный баннер с изображением продукта на синем градиентном фоне. Крупный заголовок белым шрифтом, кнопка CTA оранжевого цвета.",
    "marketing_insights": [
      "Чёткая визуальная иерархия привлекает внимание",
      "Контрастная цветовая схема выделяет CTA",
      "Минималистичный дизайн не перегружает восприятие"
    ],
    "visual_style_score": 7,
    "visual_style_analysis": "Современный корпоративный стиль с хорошим балансом элементов. Типографика читабельна, но можно улучшить отступы.",
    "recommendations": [
      "Добавить социальное доказательство (отзывы, рейтинги)",
      "Увеличить размер CTA кнопки",
      "Рассмотреть A/B тестирование цветов"
    ]
  },
  "error": null
}
```

### 3. Парсинг сайта (`POST /parse_demo`)

**Запрос:**
```bash
curl -X POST "http://localhost:8000/parse_demo" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "example.com"
  }'
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "title": "Example Domain",
    "h1": "Example Domain",
    "first_paragraph": "This domain is for use in illustrative examples in documents.",
    "analysis": {
      "strengths": ["..."],
      "weaknesses": ["..."],
      "unique_offers": ["..."],
      "recommendations": ["..."],
      "summary": "..."
    }
  },
  "error": null
}
```

### 4. Получение истории (`GET /history`)

**Запрос:**
```bash
curl -X GET "http://localhost:8000/history"
```

**Ответ:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-01-15T10:30:00",
      "request_type": "text",
      "request_summary": "Наша компания предлагает уникальные решения...",
      "response_summary": "Компания позиционирует себя как надёжного партнёра..."
    }
  ],
  "total": 1
}
```

### 5. Очистка истории (`DELETE /history`)

**Запрос:**
```bash
curl -X DELETE "http://localhost:8000/history"
```

**Ответ:**
```json
{
  "success": true,
  "message": "История очищена"
}
```

### 6. Проверка здоровья (`GET /health`)

**Запрос:**
```bash
curl -X GET "http://localhost:8000/health"
```

**Ответ:**
```json
{
  "status": "healthy",
  "service": "Competitor Monitor",
  "version": "1.0.0"
}
```

---

## Мультимодальные функции

### Поддержка текста

Приложение анализирует любой текстовый контент конкурентов:
- Описания продуктов
- Тексты с лендингов
- Рекламные объявления
- Посты в социальных сетях
- Email рассылки

**Минимальная длина текста:** 10 символов

### Поддержка изображений

Поддерживаемые форматы:
- JPEG/JPG
- PNG
- GIF
- WebP

**Что можно анализировать:**
- Рекламные баннеры
- Скриншоты сайтов
- Фотографии упаковки
- Креативы для социальных сетей
- Логотипы и фирменный стиль

**Максимальный размер:** 10MB (рекомендуется до 4MB для быстрой обработки)

### Парсинг веб-страниц

Автоматически извлекаемые элементы:
- `<title>` — заголовок страницы
- `<h1>` — главный заголовок
- Первый значимый `<p>` — первый абзац (минимум 50 символов)

**Особенности:**
- Автоматическое добавление протокола `https://`
- Следование редиректам
- Таймаут: 10 секунд
- User-Agent: Mozilla/5.0 (имитация браузера)

---

## Модели данных

### TextAnalysisRequest
```typescript
{
  text: string  // Минимум 10 символов
}
```

### ParseDemoRequest
```typescript
{
  url: string  // URL сайта для парсинга
}
```

### CompetitorAnalysis
```typescript
{
  strengths: string[]      // Сильные стороны
  weaknesses: string[]     // Слабые стороны
  unique_offers: string[]  // Уникальные предложения
  recommendations: string[] // Рекомендации
  summary: string          // Общее резюме
}
```

### ImageAnalysis
```typescript
{
  description: string           // Описание изображения
  marketing_insights: string[]  // Маркетинговые инсайты
  visual_style_score: number    // Оценка 0-10
  visual_style_analysis: string // Анализ стиля
  recommendations: string[]     // Рекомендации
}
```

### HistoryItem
```typescript
{
  id: string              // UUID записи
  timestamp: datetime     // Время запроса
  request_type: string    // "text" | "image" | "parse"
  request_summary: string // Краткое описание запроса
  response_summary: string // Краткое описание ответа
}
```

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 400 | Некорректный запрос (неверный формат, короткий текст) |
| 422 | Ошибка валидации данных |
| 500 | Внутренняя ошибка сервера |

---

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `PROXY_API_KEY` | API ключ [ProxyAPI](https://proxyapi.ru/) | - |
| `OPENAI_MODEL` | Модель для текста | `gpt-4o-mini` |
| `OPENAI_VISION_MODEL` | Модель для изображений | `gpt-4o-mini` |
| `API_HOST` | Хост сервера | `0.0.0.0` |
| `API_PORT` | Порт сервера | `8000` |

### ProxyAPI

Проект использует [ProxyAPI](https://proxyapi.ru/) — OpenAI-совместимый API для России.
- Без VPN и блокировок
- Оплата в рублях
- [Документация](https://proxyapi.ru/docs/openai-text-generation)

### Настройки истории

- Максимум записей: **10**
- Файл хранения: `history.json`
- Формат: JSON с UTF-8 кодировкой

---

## Безопасность

⚠️ **Важно:**
- Не храните API ключи в коде
- Используйте `.env` файл для секретов
- Добавьте `.env` в `.gitignore`
- В продакшене используйте HTTPS
- Настройте CORS для конкретных доменов


```

Готово! Проект переведён на [ProxyAPI](https://proxyapi.ru/docs/openai-text-generation).

## Что изменено:

1. **`config.py`** — добавлен `PROXY_API_KEY` и `base_url` для ProxyAPI
2. **`openai_service.py`** — клиент теперь использует `https://api.proxyapi.ru/openai/v1`
3. **`env.example.txt`** — обновлён шаблон переменных окружения

## Настройка:

Создайте файл `.env` в корне проекта:

```env
PROXY_API_KEY=ваш_ключ_от_proxyapi
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o-mini
```

Ключ можно получить на [proxyapi.ru](https://proxyapi.ru/).

Затем перезапустите сервер:

```powershell
python run.py
```

ProxyAPI полностью совместим с OpenAI SDK, поэтому все функции работают без изменений — генерация текста, анализ изображений (Vision API) и т.д.

```plaintext
PROXY_API_KEY=ваш_ключ_от_proxyapi
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o-mini
```

```powershell
python run.py
```

---

**User**

Добавь как можно больше логов

---

**Cursor**

Добавлю подробное логирование во все модули проекта:

```python
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
    
    # Парсер
    parser_timeout: int = 10
    parser_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


```

```python
"""
Сервис для работы с ProxyAPI (OpenAI-совместимый API)
https://proxyapi.ru/docs/openai-text-generation
"""
import base64
import json
import re
import time
import logging
from typing import Optional

from openai import OpenAI

from backend.config import settings
from backend.models.schemas import CompetitorAnalysis, ImageAnalysis

# Логгер для сервиса
logger = logging.getLogger("competitor_monitor.openai")


class OpenAIService:
    """Сервис для анализа через ProxyAPI"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("Инициализация OpenAI сервиса")
        logger.info(f"  Base URL: {settings.proxy_api_base_url}")
        logger.info(f"  Модель текста: {settings.openai_model}")
        logger.info(f"  Модель vision: {settings.openai_vision_model}")
        logger.info(f"  API ключ: {'*' * 10}...{settings.proxy_api_key[-4:] if settings.proxy_api_key else 'НЕ ЗАДАН'}")
        
        # ProxyAPI - OpenAI-совместимый API для России
        self.client = OpenAI(
            api_key=settings.proxy_api_key,
            base_url=settings.proxy_api_base_url
        )
        self.model = settings.openai_model
        self.vision_model = settings.openai_vision_model
        
        logger.info("OpenAI сервис инициализирован успешно ✓")
        logger.info("=" * 50)
    
    def _parse_json_response(self, content: str) -> dict:
        """Извлечь JSON из ответа модели"""
        logger.debug(f"Парсинг JSON ответа, длина: {len(content)} символов")
        
        # Пробуем найти JSON в markdown блоке
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)
            logger.debug("JSON найден в markdown блоке")
        
        # Пробуем найти JSON объект
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
            logger.debug("JSON объект извлечён")
        
        try:
            result = json.loads(content)
            logger.debug(f"JSON успешно распарсен, ключей: {len(result)}")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Ошибка парсинга JSON: {e}")
            logger.debug(f"Проблемный контент: {content[:200]}...")
            return {}
    
    async def analyze_text(self, text: str) -> CompetitorAnalysis:
        """Анализ текста конкурента"""
        logger.info("=" * 50)
        logger.info("📝 АНАЛИЗ ТЕКСТА КОНКУРЕНТА")
        logger.info(f"  Длина текста: {len(text)} символов")
        logger.info(f"  Превью: {text[:100]}...")
        logger.info(f"  Модель: {self.model}")
        
        system_prompt = """Ты — эксперт по конкурентному анализу. Проанализируй предоставленный текст конкурента и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
    "weaknesses": ["слабая сторона 1", "слабая сторона 2", ...],
    "unique_offers": ["уникальное предложение 1", "уникальное предложение 2", ...],
    "recommendations": ["рекомендация 1", "рекомендация 2", ...],
    "summary": "Краткое резюме анализа"
}

Важно:
- Каждый массив должен содержать 3-5 пунктов
- Пиши на русском языке
- Будь конкретен и практичен в рекомендациях"""

        start_time = time.time()
        logger.info("  Отправка запроса к API...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Проанализируй текст конкурента:\n\n{text}"}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            elapsed = time.time() - start_time
            logger.info(f"  ✓ Ответ получен за {elapsed:.2f} сек")
            
            content = response.choices[0].message.content
            logger.info(f"  Длина ответа: {len(content)} символов")
            logger.debug(f"  Использовано токенов: {response.usage.total_tokens if response.usage else 'N/A'}")
            
            data = self._parse_json_response(content)
            
            result = CompetitorAnalysis(
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                unique_offers=data.get("unique_offers", []),
                recommendations=data.get("recommendations", []),
                summary=data.get("summary", "")
            )
            
            logger.info(f"  Результат: {len(result.strengths)} сильных, {len(result.weaknesses)} слабых сторон")
            logger.info("=" * 50)
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"  ✗ Ошибка API за {elapsed:.2f} сек: {e}")
            logger.error("=" * 50)
            raise
    
    async def analyze_image(self, image_base64: str, mime_type: str = "image/jpeg") -> ImageAnalysis:
        """Анализ изображения (баннер, сайт, упаковка)"""
        logger.info("=" * 50)
        logger.info("🖼️ АНАЛИЗ ИЗОБРАЖЕНИЯ")
        logger.info(f"  Размер base64: {len(image_base64)} символов")
        logger.info(f"  MIME тип: {mime_type}")
        logger.info(f"  Модель: {self.vision_model}")
        
        system_prompt = """Ты — эксперт по визуальному маркетингу и дизайну. Проанализируй изображение конкурента (баннер, сайт, упаковка товара и т.д.) и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "description": "Детальное описание того, что изображено",
    "marketing_insights": ["инсайт 1", "инсайт 2", ...],
    "visual_style_score": 7,
    "visual_style_analysis": "Анализ визуального стиля конкурента",
    "recommendations": ["рекомендация 1", "рекомендация 2", ...]
}

Важно:
- visual_style_score от 0 до 10
- Каждый массив должен содержать 3-5 пунктов
- Пиши на русском языке
- Оценивай: цветовую палитру, типографику, композицию, UX/UI элементы"""

        start_time = time.time()
        logger.info("  Отправка запроса к Vision API...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Проанализируй это изображение конкурента с точки зрения маркетинга и дизайна:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            elapsed = time.time() - start_time
            logger.info(f"  ✓ Ответ получен за {elapsed:.2f} сек")
            
            content = response.choices[0].message.content
            logger.info(f"  Длина ответа: {len(content)} символов")
            
            data = self._parse_json_response(content)
            
            result = ImageAnalysis(
                description=data.get("description", ""),
                marketing_insights=data.get("marketing_insights", []),
                visual_style_score=data.get("visual_style_score", 5),
                visual_style_analysis=data.get("visual_style_analysis", ""),
                recommendations=data.get("recommendations", [])
            )
            
            logger.info(f"  Результат: оценка стиля {result.visual_style_score}/10")
            logger.info(f"  Инсайтов: {len(result.marketing_insights)}, рекомендаций: {len(result.recommendations)}")
            logger.info("=" * 50)
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"  ✗ Ошибка Vision API за {elapsed:.2f} сек: {e}")
            logger.error("=" * 50)
            raise
    
    async def analyze_parsed_content(
        self, 
        title: Optional[str], 
        h1: Optional[str], 
        paragraph: Optional[str]
    ) -> CompetitorAnalysis:
        """Анализ распарсенного контента сайта"""
        logger.info("📄 Анализ распарсенного контента")
        logger.info(f"  Title: {title[:50] if title else 'N/A'}...")
        logger.info(f"  H1: {h1[:50] if h1 else 'N/A'}...")
        logger.info(f"  Абзац: {paragraph[:50] if paragraph else 'N/A'}...")
        
        content_parts = []
        if title:
            content_parts.append(f"Заголовок страницы (title): {title}")
        if h1:
            content_parts.append(f"Главный заголовок (H1): {h1}")
        if paragraph:
            content_parts.append(f"Первый абзац: {paragraph}")
        
        combined_text = "\n\n".join(content_parts)
        
        if not combined_text.strip():
            logger.warning("  ⚠ Контент пустой, возвращаем пустой анализ")
            return CompetitorAnalysis(
                summary="Не удалось извлечь контент для анализа"
            )
        
        return await self.analyze_text(combined_text)
    
    async def analyze_website_screenshot(
        self,
        screenshot_base64: str,
        url: str,
        title: Optional[str] = None,
        h1: Optional[str] = None,
        first_paragraph: Optional[str] = None
    ) -> CompetitorAnalysis:
        """Комплексный анализ сайта конкурента по скриншоту"""
        logger.info("=" * 50)
        logger.info("🌐 КОМПЛЕКСНЫЙ АНАЛИЗ САЙТА")
        logger.info(f"  URL: {url}")
        logger.info(f"  Title: {title[:50] if title else 'N/A'}...")
        logger.info(f"  H1: {h1[:50] if h1 else 'N/A'}...")
        logger.info(f"  Размер скриншота: {len(screenshot_base64)} символов base64")
        logger.info(f"  Модель: {self.vision_model}")
        
        # Формируем контекст из извлечённых данных
        context_parts = [f"URL сайта: {url}"]
        if title:
            context_parts.append(f"Title страницы: {title}")
        if h1:
            context_parts.append(f"Главный заголовок (H1): {h1}")
        if first_paragraph:
            context_parts.append(f"Текст на странице: {first_paragraph[:300]}")
        
        context = "\n".join(context_parts)
        logger.debug(f"  Контекст:\n{context}")
        
        system_prompt = """Ты — эксперт по конкурентному анализу и UX/UI дизайну. Проанализируй скриншот сайта конкурента и верни структурированный JSON-ответ.

Формат ответа (строго JSON):
{
    "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
    "weaknesses": ["слабая сторона 1", "слабая сторона 2", ...],
    "unique_offers": ["уникальное предложение/фича 1", "уникальное предложение/фича 2", ...],
    "recommendations": ["рекомендация 1", "рекомендация 2", ...],
    "summary": "Комплексное резюме анализа сайта конкурента"
}

При анализе обращай внимание на:
- Дизайн и визуальный стиль (цвета, шрифты, композиция)
- UX/UI: навигация, расположение элементов, CTA кнопки
- Контент: заголовки, тексты, призывы к действию
- Уникальные торговые предложения (УТП)
- Целевая аудитория (на кого ориентирован сайт)
- Технологичность и современность дизайна

Важно:
- Каждый массив должен содержать 4-6 конкретных пунктов
- Пиши на русском языке
- Будь конкретен и практичен
- Давай actionable рекомендации"""

        start_time = time.time()
        logger.info("  Отправка скриншота в Vision API...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Проведи комплексный конкурентный анализ этого сайта:\n\n{context}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{screenshot_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            elapsed = time.time() - start_time
            logger.info(f"  ✓ Ответ получен за {elapsed:.2f} сек")
            
            content = response.choices[0].message.content
            logger.info(f"  Длина ответа: {len(content)} символов")
            
            data = self._parse_json_response(content)
            
            result = CompetitorAnalysis(
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                unique_offers=data.get("unique_offers", []),
                recommendations=data.get("recommendations", []),
                summary=data.get("summary", "")
            )
            
            logger.info(f"  Результат:")
            logger.info(f"    - Сильных сторон: {len(result.strengths)}")
            logger.info(f"    - Слабых сторон: {len(result.weaknesses)}")
            logger.info(f"    - УТП: {len(result.unique_offers)}")
            logger.info(f"    - Рекомендаций: {len(result.recommendations)}")
            logger.info(f"  Резюме: {result.summary[:100]}...")
            logger.info("=" * 50)
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"  ✗ Ошибка Vision API за {elapsed:.2f} сек: {e}")
            logger.error("=" * 50)
            raise


# Глобальный экземпляр
logger.info("Создание глобального экземпляра OpenAI сервиса...")
openai_service = OpenAIService()

```

```python
"""
Сервис для парсинга веб-страниц через Selenium Chrome
"""
import base64
import asyncio
import time
import logging
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from backend.config import settings

# Логгер для сервиса
logger = logging.getLogger("competitor_monitor.parser")


class ParserService:
    """Парсинг веб-страниц через Chrome с созданием скриншота"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("Инициализация Parser сервиса")
        logger.info(f"  Timeout: {settings.parser_timeout} сек")
        logger.info(f"  User-Agent: {settings.parser_user_agent[:50]}...")
        
        self.timeout = settings.parser_timeout
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        logger.info("Parser сервис инициализирован ✓")
        logger.info("=" * 50)
    
    def _create_driver(self) -> webdriver.Chrome:
        """Создать новый экземпляр Chrome драйвера"""
        logger.info("  🌐 Создание Chrome драйвера...")
        start_time = time.time()
        
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'--user-agent={settings.parser_user_agent}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        logger.debug("  Опции Chrome настроены")
        logger.info("  📥 Загрузка ChromeDriver...")
        
        # Автоматическая установка ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        elapsed = time.time() - start_time
        logger.info(f"  ✓ Chrome драйвер создан за {elapsed:.2f} сек")
        
        return driver
    
    def _parse_sync(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[bytes], Optional[str]]:
        """
        Синхронный парсинг URL (выполняется в отдельном потоке)
        """
        logger.info("=" * 50)
        logger.info(f"🔍 ПАРСИНГ САЙТА: {url}")
        
        driver = None
        total_start = time.time()
        
        try:
            driver = self._create_driver()
            driver.set_page_load_timeout(self.timeout)
            
            # Переходим на страницу
            logger.info(f"  📄 Загрузка страницы...")
            page_start = time.time()
            driver.get(url)
            page_elapsed = time.time() - page_start
            logger.info(f"  ✓ Страница загружена за {page_elapsed:.2f} сек")
            
            # Ждём загрузки body
            logger.info("  ⏳ Ожидание body элемента...")
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("  ✓ Body элемент найден")
            
            # Даём странице время на загрузку динамического контента
            logger.info("  ⏳ Ожидание динамического контента (2 сек)...")
            time.sleep(2)
            
            # Извлекаем title
            title = driver.title
            logger.info(f"  📌 Title: {title[:60] if title else 'N/A'}...")
            
            # Извлекаем h1
            h1 = None
            try:
                h1_element = driver.find_element(By.TAG_NAME, 'h1')
                h1 = h1_element.text.strip() if h1_element.text else None
                logger.info(f"  📌 H1: {h1[:60] if h1 else 'N/A'}...")
            except Exception as e:
                logger.debug(f"  H1 не найден: {e}")
            
            # Извлекаем первый абзац
            first_paragraph = None
            try:
                paragraphs = driver.find_elements(By.TAG_NAME, 'p')
                logger.debug(f"  Найдено абзацев: {len(paragraphs)}")
                for i, p in enumerate(paragraphs):
                    text = p.text.strip() if p.text else ""
                    if len(text) > 50:
                        first_paragraph = text[:500]
                        logger.info(f"  📌 Первый абзац (p[{i}]): {first_paragraph[:60]}...")
                        break
            except Exception as e:
                logger.debug(f"  Абзацы не найдены: {e}")
            
            # Делаем скриншот
            logger.info("  📸 Создание скриншота...")
            screenshot_start = time.time()
            screenshot_bytes = driver.get_screenshot_as_png()
            screenshot_elapsed = time.time() - screenshot_start
            screenshot_size_kb = len(screenshot_bytes) / 1024
            logger.info(f"  ✓ Скриншот создан за {screenshot_elapsed:.2f} сек ({screenshot_size_kb:.1f} KB)")
            
            total_elapsed = time.time() - total_start
            logger.info(f"  ✅ ПАРСИНГ ЗАВЕРШЁН за {total_elapsed:.2f} сек")
            logger.info("=" * 50)
            
            return title, h1, first_paragraph, screenshot_bytes, None
            
        except TimeoutException:
            total_elapsed = time.time() - total_start
            logger.error(f"  ✗ TIMEOUT за {total_elapsed:.2f} сек")
            logger.error("=" * 50)
            return None, None, None, None, "Превышено время ожидания загрузки страницы"
            
        except WebDriverException as e:
            total_elapsed = time.time() - total_start
            error_msg = str(e)
            logger.error(f"  ✗ WebDriver ошибка за {total_elapsed:.2f} сек")
            logger.error(f"  Детали: {error_msg[:200]}")
            logger.error("=" * 50)
            
            if 'net::ERR_NAME_NOT_RESOLVED' in error_msg:
                return None, None, None, None, "Не удалось найти сайт по указанному адресу"
            elif 'net::ERR_CONNECTION_REFUSED' in error_msg:
                return None, None, None, None, "Соединение отклонено сервером"
            elif 'net::ERR_CONNECTION_TIMED_OUT' in error_msg:
                return None, None, None, None, "Превышено время ожидания соединения"
            else:
                return None, None, None, None, f"Ошибка браузера: {error_msg[:200]}"
                
        except Exception as e:
            total_elapsed = time.time() - total_start
            logger.error(f"  ✗ Неизвестная ошибка за {total_elapsed:.2f} сек: {e}")
            logger.error("=" * 50)
            return None, None, None, None, f"Ошибка при загрузке страницы: {str(e)[:200]}"
            
        finally:
            if driver:
                try:
                    logger.debug("  Закрытие драйвера...")
                    driver.quit()
                    logger.debug("  ✓ Драйвер закрыт")
                except Exception as e:
                    logger.warning(f"  Ошибка при закрытии драйвера: {e}")
    
    async def parse_url(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[bytes], Optional[str]]:
        """
        Асинхронный парсинг URL через Chrome
        """
        # Добавляем протокол если его нет
        original_url = url
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            logger.info(f"  URL дополнен протоколом: {original_url} -> {url}")
        
        logger.info(f"🚀 Запуск асинхронного парсинга: {url}")
        
        # Запускаем синхронный парсинг в отдельном потоке
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor,
            self._parse_sync,
            url
        )
        
        return result
    
    def screenshot_to_base64(self, screenshot_bytes: bytes) -> str:
        """Конвертировать скриншот в base64"""
        base64_str = base64.b64encode(screenshot_bytes).decode('utf-8')
        logger.debug(f"Скриншот конвертирован в base64: {len(base64_str)} символов")
        return base64_str
    
    async def close(self):
        """Закрыть executor"""
        logger.info("Закрытие Parser сервиса...")
        self._executor.shutdown(wait=False)
        logger.info("Parser сервис закрыт ✓")


# Глобальный экземпляр
logger.info("Создание глобального экземпляра Parser сервиса...")
parser_service = ParserService()

```

```python
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

```

```python
"""
Главный модуль FastAPI приложения
Мониторинг конкурентов - MVP ассистент
"""
import base64
import time
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from backend.config import settings
from backend.models.schemas import (
    TextAnalysisRequest,
    TextAnalysisResponse,
    ImageAnalysisResponse,
    ParseDemoRequest,
    ParseDemoResponse,
    ParsedContent,
    HistoryResponse
)
from backend.services.openai_service import openai_service
from backend.services.parser_service import parser_service
from backend.services.history_service import history_service

# Логгер для API
logger = logging.getLogger("competitor_monitor.api")

# Инициализация приложения
logger.info("=" * 60)
logger.info("🚀 ЗАПУСК ПРИЛОЖЕНИЯ: Мониторинг конкурентов")
logger.info("=" * 60)

app = FastAPI(
    title="Мониторинг конкурентов",
    description="MVP ассистент для анализа конкурентов с поддержкой текста и изображений",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS middleware добавлен ✓")


# === Middleware для логирования запросов ===

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование всех HTTP запросов"""
    start_time = time.time()
    
    # Логируем входящий запрос
    logger.info(f"➡️  {request.method} {request.url.path}")
    if request.query_params:
        logger.debug(f"    Query params: {dict(request.query_params)}")
    
    # Выполняем запрос
    response = await call_next(request)
    
    # Логируем ответ
    elapsed = time.time() - start_time
    status_emoji = "✅" if response.status_code < 400 else "❌"
    logger.info(f"{status_emoji} {request.method} {request.url.path} -> {response.status_code} ({elapsed:.3f}s)")
    
    return response


# === События жизненного цикла ===

@app.on_event("startup")
async def startup_event():
    """Событие при запуске сервера"""
    logger.info("=" * 60)
    logger.info("🟢 СЕРВЕР ЗАПУЩЕН")
    logger.info(f"  Адрес: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"  Документация: http://localhost:{settings.api_port}/docs")
    logger.info(f"  Модель текста: {settings.openai_model}")
    logger.info(f"  Модель vision: {settings.openai_vision_model}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Закрытие ресурсов при остановке сервера"""
    logger.info("=" * 60)
    logger.info("🔴 ОСТАНОВКА СЕРВЕРА")
    logger.info("  Закрытие Parser сервиса...")
    await parser_service.close()
    logger.info("  ✓ Все ресурсы освобождены")
    logger.info("=" * 60)


# === Эндпоинты ===

@app.get("/")
async def root():
    """Главная страница - отдаём фронтенд"""
    logger.debug("Запрос главной страницы")
    return FileResponse("frontend/index.html")


@app.post("/analyze_text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Анализ текста конкурента
    """
    logger.info("=" * 50)
    logger.info("📝 API: АНАЛИЗ ТЕКСТА")
    logger.info(f"  Длина текста: {len(request.text)} символов")
    logger.info(f"  Превью: {request.text[:80]}...")
    
    try:
        start_time = time.time()
        
        analysis = await openai_service.analyze_text(request.text)
        
        elapsed = time.time() - start_time
        logger.info(f"  ✓ Анализ завершён за {elapsed:.2f} сек")
        
        # Сохраняем в историю
        logger.info("  💾 Сохранение в историю...")
        history_service.add_entry(
            request_type="text",
            request_summary=request.text[:100] + "..." if len(request.text) > 100 else request.text,
            response_summary=analysis.summary
        )
        
        logger.info("  ✅ УСПЕХ: Анализ текста завершён")
        logger.info("=" * 50)
        
        return TextAnalysisResponse(
            success=True,
            analysis=analysis
        )
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return TextAnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/analyze_image", response_model=ImageAnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    Анализ изображения конкурента
    """
    logger.info("=" * 50)
    logger.info("🖼️ API: АНАЛИЗ ИЗОБРАЖЕНИЯ")
    logger.info(f"  Имя файла: {file.filename}")
    logger.info(f"  Тип: {file.content_type}")
    
    # Проверяем тип файла
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        logger.warning(f"  ⚠ Неподдерживаемый тип файла: {file.content_type}")
        logger.info("=" * 50)
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(allowed_types)}"
        )
    
    try:
        start_time = time.time()
        
        # Читаем и кодируем изображение
        logger.info("  📥 Чтение файла...")
        content = await file.read()
        file_size_kb = len(content) / 1024
        logger.info(f"  Размер файла: {file_size_kb:.1f} KB")
        
        image_base64 = base64.b64encode(content).decode('utf-8')
        logger.info(f"  Base64 размер: {len(image_base64)} символов")
        
        # Анализируем
        logger.info("  🔍 Отправка на анализ...")
        analysis = await openai_service.analyze_image(
            image_base64=image_base64,
            mime_type=file.content_type
        )
        
        elapsed = time.time() - start_time
        logger.info(f"  ✓ Анализ завершён за {elapsed:.2f} сек")
        
        # Сохраняем в историю
        logger.info("  💾 Сохранение в историю...")
        history_service.add_entry(
            request_type="image",
            request_summary=f"Изображение: {file.filename}",
            response_summary=analysis.description[:200] if analysis.description else "Анализ изображения"
        )
        
        logger.info("  ✅ УСПЕХ: Анализ изображения завершён")
        logger.info("=" * 50)
        
        return ImageAnalysisResponse(
            success=True,
            analysis=analysis
        )
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return ImageAnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/parse_demo", response_model=ParseDemoResponse)
async def parse_demo(request: ParseDemoRequest):
    """
    Парсинг и анализ сайта конкурента через Chrome
    """
    logger.info("=" * 50)
    logger.info("🌐 API: ПАРСИНГ САЙТА")
    logger.info(f"  URL: {request.url}")
    
    try:
        total_start = time.time()
        
        # Открываем страницу в Chrome и делаем скриншот
        logger.info("  🔍 Запуск парсинга...")
        parse_start = time.time()
        title, h1, first_paragraph, screenshot_bytes, error = await parser_service.parse_url(request.url)
        parse_elapsed = time.time() - parse_start
        logger.info(f"  ✓ Парсинг завершён за {parse_elapsed:.2f} сек")
        
        if error:
            logger.error(f"  ❌ Ошибка парсинга: {error}")
            logger.info("=" * 50)
            return ParseDemoResponse(
                success=False,
                error=error
            )
        
        logger.info(f"  📌 Title: {title[:50] if title else 'N/A'}...")
        logger.info(f"  📌 H1: {h1[:50] if h1 else 'N/A'}...")
        logger.info(f"  📌 Screenshot: {len(screenshot_bytes) / 1024:.1f} KB" if screenshot_bytes else "  📌 Screenshot: N/A")
        
        # Конвертируем скриншот в base64
        screenshot_base64 = parser_service.screenshot_to_base64(screenshot_bytes) if screenshot_bytes else None
        
        # Анализируем сайт через Vision API (скриншот + контекст)
        logger.info("  🤖 Запуск AI анализа...")
        ai_start = time.time()
        
        if screenshot_base64:
            analysis = await openai_service.analyze_website_screenshot(
                screenshot_base64=screenshot_base64,
                url=request.url,
                title=title,
                h1=h1,
                first_paragraph=first_paragraph
            )
        else:
            logger.warning("  ⚠ Скриншот недоступен, fallback на текстовый анализ")
            analysis = await openai_service.analyze_parsed_content(
                title=title,
                h1=h1,
                paragraph=first_paragraph
            )
        
        ai_elapsed = time.time() - ai_start
        logger.info(f"  ✓ AI анализ завершён за {ai_elapsed:.2f} сек")
        
        parsed_content = ParsedContent(
            url=request.url,
            title=title,
            h1=h1,
            first_paragraph=first_paragraph,
            analysis=analysis
        )
        
        # Сохраняем в историю
        logger.info("  💾 Сохранение в историю...")
        history_service.add_entry(
            request_type="parse",
            request_summary=f"URL: {request.url}",
            response_summary=analysis.summary[:100] if analysis.summary else f"Title: {title or 'N/A'}"
        )
        
        total_elapsed = time.time() - total_start
        logger.info(f"  ✅ УСПЕХ: Парсинг и анализ завершён за {total_elapsed:.2f} сек")
        logger.info(f"    - Парсинг: {parse_elapsed:.2f} сек")
        logger.info(f"    - AI анализ: {ai_elapsed:.2f} сек")
        logger.info("=" * 50)
        
        return ParseDemoResponse(
            success=True,
            data=parsed_content
        )
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return ParseDemoResponse(
            success=False,
            error=str(e)
        )


@app.get("/history", response_model=HistoryResponse)
async def get_history():
    """
    Получить историю последних 10 запросов
    """
    logger.info("📋 API: Получение истории")
    items = history_service.get_history()
    logger.info(f"  Записей: {len(items)}")
    return HistoryResponse(
        items=items,
        total=len(items)
    )


@app.delete("/history")
async def clear_history():
    """
    Очистить историю запросов
    """
    logger.info("🗑️ API: Очистка истории")
    history_service.clear_history()
    logger.info("  ✓ История очищена")
    return {"success": True, "message": "История очищена"}


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    logger.debug("❤️ Health check")
    return {
        "status": "healthy",
        "service": "Competitor Monitor",
        "version": "1.0.0"
    }


# Статические файлы для фронтенда
app.mount("/static", StaticFiles(directory="frontend"), name="static")
logger.info("Статические файлы подключены: /static -> frontend/")


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

```

```python
"""
Скрипт запуска приложения Мониторинг конкурентов
"""
import uvicorn
import logging
from backend.config import settings, logger

# Настраиваем уровень логирования
logging.getLogger("competitor_monitor").setLevel(logging.INFO)

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("🚀 МОНИТОРИНГ КОНКУРЕНТОВ - AI Ассистент")
    print("=" * 60)
    print()
    print(f"📍 Веб-интерфейс:  http://localhost:{settings.api_port}")
    print(f"📚 Документация:   http://localhost:{settings.api_port}/docs")
    print(f"📖 ReDoc:          http://localhost:{settings.api_port}/redoc")
    print()
    print(f"🤖 Модель текста:  {settings.openai_model}")
    print(f"👁️ Модель vision:  {settings.openai_vision_model}")
    print(f"🔑 API ключ:       {'✓ Настроен' if settings.proxy_api_key else '✗ НЕ ЗАДАН!'}")
    print()
    print("-" * 60)
    print("Логи запросов будут отображаться ниже...")
    print("-" * 60)
    print()
    
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )

```

Готово! Добавил подробное логирование во все модули. Теперь при работе вы увидите:

## Примеры логов

**Запуск сервера:**
```
============================================================
🚀 МОНИТОРИНГ КОНКУРЕНТОВ - AI Ассистент
============================================================

📍 Веб-интерфейс:  http://localhost:8000
📚 Документация:   http://localhost:8000/docs
🤖 Модель текста:  gpt-4o-mini
👁️ Модель vision:  gpt-4o-mini
🔑 API ключ:       ✓ Настроен
```

**HTTP запросы:**
```
➡️  POST /analyze_text
✅ POST /analyze_text -> 200 (3.245s)
```

**Анализ текста:**
```
==================================================
📝 АНАЛИЗ ТЕКСТА КОНКУРЕНТА
  Длина текста: 450 символов
  Превью: Наша компания предлагает...
  Модель: gpt-4o-mini
  Отправка запроса к API...
  ✓ Ответ получен за 2.34 сек
  Результат: 4 сильных, 3 слабых сторон
==================================================
```

**Парсинг сайта:**
```
==================================================
🔍 ПАРСИНГ САЙТА: https://example.com
  🌐 Создание Chrome драйвера...
  📥 Загрузка ChromeDriver...
  ✓ Chrome драйвер создан за 1.23 сек
  📄 Загрузка страницы...
  ✓ Страница загружена за 2.45 сек
  📌 Title: Example Domain...
  📸 Создание скриншота...
  ✓ Скриншот создан за 0.15 сек (245.3 KB)
  ✅ ПАРСИНГ ЗАВЕРШЁН за 5.67 сек
==================================================
```

Перезапустите сервер командой `python run.py` чтобы увидеть логи.

```plaintext
============================================================
🚀 МОНИТОРИНГ КОНКУРЕНТОВ - AI Ассистент
============================================================

📍 Веб-интерфейс:  http://localhost:8000
📚 Документация:   http://localhost:8000/docs
🤖 Модель текста:  gpt-4o-mini
👁️ Модель vision:  gpt-4o-mini
🔑 API ключ:       ✓ Настроен
```

```plaintext
➡️  POST /analyze_text
✅ POST /analyze_text -> 200 (3.245s)
```

```plaintext
==================================================
📝 АНАЛИЗ ТЕКСТА КОНКУРЕНТА
  Длина текста: 450 символов
  Превью: Наша компания предлагает...
  Модель: gpt-4o-mini
  Отправка запроса к API...
  ✓ Ответ получен за 2.34 сек
  Результат: 4 сильных, 3 слабых сторон
==================================================
```

```plaintext
==================================================
🔍 ПАРСИНГ САЙТА: https://example.com
  🌐 Создание Chrome драйвера...
  📥 Загрузка ChromeDriver...
  ✓ Chrome драйвер создан за 1.23 сек
  📄 Загрузка страницы...
  ✓ Страница загружена за 2.45 сек
  📌 Title: Example Domain...
  📸 Создание скриншота...
  ✓ Скриншот создан за 0.15 сек (245.3 KB)
  ✅ ПАРСИНГ ЗАВЕРШЁН за 5.67 сек
==================================================
```

---

**User**

В отдельной директории сделай приложение на PyQT6



Оно будет полностью повторять сайт, и заверни всё это в .exe для windows

---

**Cursor**

Создам десктопное приложение на PyQt6 в отдельной директории:

```pip-requirements
PyQt6>=6.6.0
requests>=2.31.0
Pillow>=10.0.0
pyinstaller>=6.0.0

```

```python
"""
Стили для PyQt6 приложения - тёмная тема с cyan акцентами
"""

DARK_THEME = """
/* === Основные стили === */
QMainWindow, QWidget {
    background-color: #0a0f1c;
    color: #f1f5f9;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}

/* === Sidebar === */
#sidebar {
    background-color: #111827;
    border-right: 1px solid #1e293b;
}

#logo {
    color: #06b6d4;
    font-size: 18px;
    font-weight: bold;
    padding: 20px;
    border-bottom: 1px solid #1e293b;
}

/* === Navigation Buttons === */
QPushButton#navButton {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 8px;
    padding: 14px 16px;
    text-align: left;
    font-size: 14px;
}

QPushButton#navButton:hover {
    background-color: #243049;
    color: #f1f5f9;
}

QPushButton#navButton:checked {
    background-color: rgba(6, 182, 212, 0.2);
    color: #22d3ee;
    border: 1px solid rgba(6, 182, 212, 0.3);
}

/* === Cards === */
QFrame#card {
    background-color: #1a2234;
    border: 1px solid #1e293b;
    border-radius: 12px;
}

QFrame#card:hover {
    border-color: #334155;
}

/* === Labels === */
QLabel#title {
    font-size: 24px;
    font-weight: bold;
    color: #f1f5f9;
}

QLabel#subtitle {
    font-size: 14px;
    color: #94a3b8;
}

QLabel#cardTitle {
    font-size: 16px;
    font-weight: 600;
    color: #f1f5f9;
}

QLabel#cardDescription {
    font-size: 13px;
    color: #94a3b8;
}

QLabel#sectionTitle {
    font-size: 14px;
    font-weight: 600;
    color: #22d3ee;
    margin-bottom: 8px;
}

/* === Text Input === */
QTextEdit, QLineEdit {
    background-color: #0d1320;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 12px;
    color: #f1f5f9;
    font-size: 14px;
}

QTextEdit:focus, QLineEdit:focus {
    border-color: #06b6d4;
}

QTextEdit::placeholder, QLineEdit::placeholder {
    color: #64748b;
}

/* === Primary Button === */
QPushButton#primaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #06b6d4, stop:1 #22d3ee);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 14px 24px;
    font-size: 14px;
    font-weight: 500;
}

QPushButton#primaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0891b2, stop:1 #06b6d4);
}

QPushButton#primaryButton:disabled {
    background-color: #334155;
    color: #64748b;
}

/* === Secondary Button === */
QPushButton#secondaryButton {
    background-color: #243049;
    color: #94a3b8;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 12px 20px;
    font-size: 14px;
}

QPushButton#secondaryButton:hover {
    background-color: #334155;
    color: #f1f5f9;
}

/* === Upload Zone === */
QFrame#uploadZone {
    background-color: #0d1320;
    border: 2px dashed #334155;
    border-radius: 12px;
    min-height: 200px;
}

QFrame#uploadZone:hover {
    border-color: #06b6d4;
    background-color: rgba(6, 182, 212, 0.05);
}

/* === Results === */
QFrame#resultsCard {
    background-color: #1a2234;
    border: 1px solid #06b6d4;
    border-radius: 12px;
}

QFrame#resultBlock {
    background-color: #111827;
    border-left: 3px solid #06b6d4;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
}

/* === History === */
QFrame#historyItem {
    background-color: #111827;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 12px;
}

QFrame#historyItem:hover {
    border-color: #334155;
}

/* === ScrollArea === */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollBar:vertical {
    background-color: #111827;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #334155;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* === Progress/Loading === */
QProgressBar {
    background-color: #0d1320;
    border: none;
    border-radius: 4px;
    height: 8px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #22d3ee);
    border-radius: 4px;
}

/* === Tab Widget === */
QTabWidget::pane {
    border: none;
    background-color: transparent;
}

QTabBar::tab {
    background-color: transparent;
    color: #94a3b8;
    padding: 12px 20px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #22d3ee;
    border-bottom: 2px solid #06b6d4;
}

QTabBar::tab:hover:!selected {
    color: #f1f5f9;
}

/* === Status === */
QLabel#statusActive {
    color: #10b981;
}

QLabel#statusError {
    color: #ef4444;
}

/* === Tooltips === */
QToolTip {
    background-color: #1a2234;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 8px;
}
"""

```

```python
"""
API клиент для связи с backend
"""
import requests
from typing import Optional, Dict, Any
import base64


class APIClient:
    """Клиент для работы с API backend"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 120  # 2 минуты для долгих операций
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнить HTTP запрос"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Не удалось подключиться к серверу. Убедитесь, что backend запущен."}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Превышено время ожидания ответа от сервера."}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"HTTP ошибка: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_health(self) -> bool:
        """Проверить доступность сервера"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Анализ текста конкурента"""
        return self._request(
            "POST",
            "/analyze_text",
            json={"text": text}
        )
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Анализ изображения конкурента"""
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (image_path.split('/')[-1], f, 'image/jpeg')}
                return self._request("POST", "/analyze_image", files=files)
        except FileNotFoundError:
            return {"success": False, "error": "Файл не найден"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_image_bytes(self, image_bytes: bytes, filename: str = "image.jpg") -> Dict[str, Any]:
        """Анализ изображения из bytes"""
        files = {'file': (filename, image_bytes, 'image/jpeg')}
        return self._request("POST", "/analyze_image", files=files)
    
    def parse_demo(self, url: str) -> Dict[str, Any]:
        """Парсинг и анализ сайта"""
        return self._request(
            "POST",
            "/parse_demo",
            json={"url": url}
        )
    
    def get_history(self) -> Dict[str, Any]:
        """Получить историю запросов"""
        return self._request("GET", "/history")
    
    def clear_history(self) -> Dict[str, Any]:
        """Очистить историю"""
        return self._request("DELETE", "/history")


# Глобальный экземпляр
api_client = APIClient()

```

```python
"""
Мониторинг конкурентов - Desktop приложение на PyQt6
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QFrame, QScrollArea,
    QFileDialog, QStackedWidget, QSplitter, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon, QDragEnterEvent, QDropEvent

from styles import DARK_THEME
from api_client import api_client


class WorkerThread(QThread):
    """Поток для выполнения API запросов"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class DropZone(QFrame):
    """Зона для drag & drop изображений"""
    fileDropped = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("uploadZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_label = QLabel("📁")
        self.icon_label.setStyleSheet("font-size: 48px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.text_label = QLabel("Перетащите изображение или нажмите для выбора")
        self.text_label.setStyleSheet("color: #94a3b8; font-size: 14px;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.hint_label = QLabel("PNG, JPG, GIF, WEBP до 10MB")
        self.hint_label.setStyleSheet("color: #64748b; font-size: 12px;")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.hide()
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addWidget(self.hint_label)
        layout.addWidget(self.preview_label)
        
        self.selected_file = None
    
    def mousePressEvent(self, event):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение",
            "",
            "Изображения (*.png *.jpg *.jpeg *.gif *.webp)"
        )
        if file_path:
            self.set_file(file_path)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("QFrame#uploadZone { border-color: #06b6d4; background-color: rgba(6, 182, 212, 0.1); }")
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
    
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                self.set_file(file_path)
    
    def set_file(self, file_path: str):
        self.selected_file = file_path
        
        # Показываем превью
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(pixmap)
            self.preview_label.show()
            self.icon_label.hide()
            self.text_label.setText(Path(file_path).name)
            self.hint_label.setText("Нажмите для замены")
        
        self.fileDropped.emit(file_path)
    
    def clear(self):
        self.selected_file = None
        self.preview_label.hide()
        self.icon_label.show()
        self.text_label.setText("Перетащите изображение или нажмите для выбора")
        self.hint_label.setText("PNG, JPG, GIF, WEBP до 10MB")


class ResultBlock(QFrame):
    """Блок результата анализа"""
    def __init__(self, title: str, items: list, icon: str = "→"):
        super().__init__()
        self.setObjectName("resultBlock")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)
        
        for item in items:
            item_label = QLabel(f"{icon} {item}")
            item_label.setWordWrap(True)
            item_label.setStyleSheet("color: #94a3b8; margin-left: 8px; line-height: 1.5;")
            layout.addWidget(item_label)


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Мониторинг конкурентов | AI Ассистент")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Применяем стили
        self.setStyleSheet(DARK_THEME)
        
        # Главный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.setup_sidebar(main_layout)
        
        # Content area
        self.setup_content(main_layout)
        
        # Текущий worker
        self.current_worker = None
        
        # Проверяем подключение к серверу
        self.check_server_connection()
    
    def setup_sidebar(self, parent_layout):
        """Создание боковой панели"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo
        logo = QLabel("⚡ CompetitorAI")
        logo.setObjectName("logo")
        layout.addWidget(logo)
        
        # Navigation
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(4)
        
        self.nav_buttons = []
        nav_items = [
            ("📝 Анализ текста", 0),
            ("🖼️ Анализ изображений", 1),
            ("🌐 Парсинг сайта", 2),
            ("📋 История", 3)
        ]
        
        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self.switch_tab(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        self.nav_buttons[0].setChecked(True)
        
        nav_layout.addStretch()
        
        # Status
        self.status_label = QLabel("● Проверка подключения...")
        self.status_label.setStyleSheet("color: #f59e0b; padding: 16px;")
        nav_layout.addWidget(self.status_label)
        
        layout.addWidget(nav_widget)
        parent_layout.addWidget(sidebar)
    
    def setup_content(self, parent_layout):
        """Создание области контента"""
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 32, 40, 32)
        
        # Header
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 24)
        
        title = QLabel("Мониторинг конкурентов")
        title.setObjectName("title")
        
        subtitle = QLabel("AI-ассистент для анализа конкурентной среды")
        subtitle.setObjectName("subtitle")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        content_layout.addWidget(header)
        
        # Stacked widget для вкладок
        self.stacked_widget = QStackedWidget()
        
        # Добавляем вкладки
        self.stacked_widget.addWidget(self.create_text_tab())
        self.stacked_widget.addWidget(self.create_image_tab())
        self.stacked_widget.addWidget(self.create_parse_tab())
        self.stacked_widget.addWidget(self.create_history_tab())
        
        content_layout.addWidget(self.stacked_widget)
        
        # Results area
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.hide()
        
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_scroll.setWidget(self.results_widget)
        
        content_layout.addWidget(self.results_scroll)
        
        # Loading indicator
        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setFixedWidth(300)
        
        self.loading_label = QLabel("Анализирую данные...")
        self.loading_label.setStyleSheet("color: #94a3b8; font-size: 16px;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        loading_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self.loading_label)
        
        self.loading_widget.hide()
        content_layout.addWidget(self.loading_widget)
        
        parent_layout.addWidget(content_widget)
    
    def create_text_tab(self) -> QWidget:
        """Вкладка анализа текста"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Анализ текста конкурента")
        title.setObjectName("cardTitle")
        
        desc = QLabel("Вставьте текст с сайта конкурента, из рекламы или описания продукта")
        desc.setObjectName("cardDescription")
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Вставьте текст конкурента для анализа...\n\nНапример: описание продукта, текст с лендинга, рекламное объявление...")
        self.text_input.setMinimumHeight(200)
        
        self.analyze_text_btn = QPushButton("⚡ Проанализировать")
        self.analyze_text_btn.setObjectName("primaryButton")
        self.analyze_text_btn.clicked.connect(self.analyze_text)
        
        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.text_input)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.analyze_text_btn)
        
        layout.addWidget(card)
        layout.addStretch()
        
        return widget
    
    def create_image_tab(self) -> QWidget:
        """Вкладка анализа изображений"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Анализ изображений")
        title.setObjectName("cardTitle")
        
        desc = QLabel("Загрузите скриншот сайта, баннер или фото упаковки конкурента")
        desc.setObjectName("cardDescription")
        
        self.drop_zone = DropZone()
        
        self.analyze_image_btn = QPushButton("⚡ Проанализировать")
        self.analyze_image_btn.setObjectName("primaryButton")
        self.analyze_image_btn.clicked.connect(self.analyze_image)
        
        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.drop_zone)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.analyze_image_btn)
        
        layout.addWidget(card)
        layout.addStretch()
        
        return widget
    
    def create_parse_tab(self) -> QWidget:
        """Вкладка парсинга сайта"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Парсинг сайта конкурента")
        title.setObjectName("cardTitle")
        
        desc = QLabel("Введите URL сайта для автоматического извлечения и анализа контента")
        desc.setObjectName("cardDescription")
        
        # URL input
        url_layout = QHBoxLayout()
        
        prefix = QLabel("https://")
        prefix.setStyleSheet("background-color: #243049; padding: 12px 16px; border-radius: 8px 0 0 8px; color: #64748b;")
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("example.com")
        self.url_input.setStyleSheet("border-radius: 0 8px 8px 0;")
        
        url_layout.addWidget(prefix)
        url_layout.addWidget(self.url_input)
        
        self.parse_btn = QPushButton("⚡ Парсить и анализировать")
        self.parse_btn.setObjectName("primaryButton")
        self.parse_btn.clicked.connect(self.parse_site)
        
        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        card_layout.addSpacing(16)
        card_layout.addLayout(url_layout)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.parse_btn)
        
        layout.addWidget(card)
        layout.addStretch()
        
        return widget
    
    def create_history_tab(self) -> QWidget:
        """Вкладка истории"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header with clear button
        header = QHBoxLayout()
        
        title = QLabel("История запросов")
        title.setObjectName("cardTitle")
        
        self.clear_history_btn = QPushButton("🗑️ Очистить")
        self.clear_history_btn.setObjectName("secondaryButton")
        self.clear_history_btn.clicked.connect(self.clear_history)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.clear_history_btn)
        
        layout.addLayout(header)
        
        # History scroll area
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        
        self.history_widget = QWidget()
        self.history_layout = QVBoxLayout(self.history_widget)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.history_scroll.setWidget(self.history_widget)
        layout.addWidget(self.history_scroll)
        
        return widget
    
    def switch_tab(self, index: int):
        """Переключение вкладок"""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        
        self.stacked_widget.setCurrentIndex(index)
        self.results_scroll.hide()
        
        # Загружаем историю при переключении на вкладку
        if index == 3:
            self.load_history()
    
    def check_server_connection(self):
        """Проверка подключения к серверу"""
        if api_client.check_health():
            self.status_label.setText("● Система активна")
            self.status_label.setStyleSheet("color: #10b981; padding: 16px;")
        else:
            self.status_label.setText("● Сервер недоступен")
            self.status_label.setStyleSheet("color: #ef4444; padding: 16px;")
    
    def show_loading(self, message: str = "Анализирую данные..."):
        """Показать индикатор загрузки"""
        self.loading_label.setText(message)
        self.loading_widget.show()
        self.results_scroll.hide()
        
        # Отключаем кнопки
        self.analyze_text_btn.setEnabled(False)
        self.analyze_image_btn.setEnabled(False)
        self.parse_btn.setEnabled(False)
    
    def hide_loading(self):
        """Скрыть индикатор загрузки"""
        self.loading_widget.hide()
        
        # Включаем кнопки
        self.analyze_text_btn.setEnabled(True)
        self.analyze_image_btn.setEnabled(True)
        self.parse_btn.setEnabled(True)
    
    def show_results(self, analysis: dict, result_type: str = "text"):
        """Отображение результатов анализа"""
        # Очищаем предыдущие результаты
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Заголовок
        title = QLabel("📊 Результаты анализа")
        title.setObjectName("cardTitle")
        title.setStyleSheet("font-size: 18px; margin-bottom: 16px;")
        self.results_layout.addWidget(title)
        
        if result_type == "text" or result_type == "parse":
            # Сильные стороны
            if analysis.get("strengths"):
                block = ResultBlock("✅ Сильные стороны", analysis["strengths"])
                self.results_layout.addWidget(block)
            
            # Слабые стороны
            if analysis.get("weaknesses"):
                block = ResultBlock("⚠️ Слабые стороны", analysis["weaknesses"])
                self.results_layout.addWidget(block)
            
            # Уникальные предложения
            if analysis.get("unique_offers"):
                block = ResultBlock("⭐ Уникальные предложения", analysis["unique_offers"])
                self.results_layout.addWidget(block)
            
            # Рекомендации
            if analysis.get("recommendations"):
                block = ResultBlock("💡 Рекомендации", analysis["recommendations"])
                self.results_layout.addWidget(block)
            
            # Резюме
            if analysis.get("summary"):
                summary_frame = QFrame()
                summary_frame.setObjectName("resultBlock")
                summary_frame.setStyleSheet("QFrame#resultBlock { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(6, 182, 212, 0.1), stop:1 rgba(139, 92, 246, 0.1)); }")
                summary_layout = QVBoxLayout(summary_frame)
                
                summary_title = QLabel("📝 Резюме")
                summary_title.setObjectName("sectionTitle")
                
                summary_text = QLabel(analysis["summary"])
                summary_text.setWordWrap(True)
                summary_text.setStyleSheet("color: #f1f5f9; font-size: 15px; line-height: 1.6;")
                
                summary_layout.addWidget(summary_title)
                summary_layout.addWidget(summary_text)
                self.results_layout.addWidget(summary_frame)
        
        elif result_type == "image":
            # Описание
            if analysis.get("description"):
                desc_frame = QFrame()
                desc_frame.setObjectName("resultBlock")
                desc_layout = QVBoxLayout(desc_frame)
                
                desc_title = QLabel("🖼️ Описание изображения")
                desc_title.setObjectName("sectionTitle")
                
                desc_text = QLabel(analysis["description"])
                desc_text.setWordWrap(True)
                desc_text.setStyleSheet("color: #94a3b8;")
                
                desc_layout.addWidget(desc_title)
                desc_layout.addWidget(desc_text)
                self.results_layout.addWidget(desc_frame)
            
            # Оценка стиля
            if "visual_style_score" in analysis:
                score = analysis["visual_style_score"]
                score_frame = QFrame()
                score_frame.setObjectName("resultBlock")
                score_layout = QVBoxLayout(score_frame)
                
                score_title = QLabel("⭐ Оценка визуального стиля")
                score_title.setObjectName("sectionTitle")
                
                score_value = QLabel(f"{score}/10")
                score_value.setStyleSheet("font-size: 32px; font-weight: bold; color: #22d3ee;")
                
                if analysis.get("visual_style_analysis"):
                    score_desc = QLabel(analysis["visual_style_analysis"])
                    score_desc.setWordWrap(True)
                    score_desc.setStyleSheet("color: #94a3b8;")
                    score_layout.addWidget(score_desc)
                
                score_layout.addWidget(score_title)
                score_layout.addWidget(score_value)
                self.results_layout.addWidget(score_frame)
            
            # Маркетинговые инсайты
            if analysis.get("marketing_insights"):
                block = ResultBlock("💡 Маркетинговые инсайты", analysis["marketing_insights"])
                self.results_layout.addWidget(block)
            
            # Рекомендации
            if analysis.get("recommendations"):
                block = ResultBlock("📋 Рекомендации", analysis["recommendations"])
                self.results_layout.addWidget(block)
        
        self.results_layout.addStretch()
        self.results_scroll.show()
    
    def show_error(self, message: str):
        """Показать сообщение об ошибке"""
        QMessageBox.critical(self, "Ошибка", message)
    
    # === API методы ===
    
    def analyze_text(self):
        """Анализ текста"""
        text = self.text_input.toPlainText().strip()
        
        if len(text) < 10:
            self.show_error("Введите текст минимум 10 символов")
            return
        
        self.show_loading("Анализирую текст...")
        
        self.current_worker = WorkerThread(api_client.analyze_text, text)
        self.current_worker.finished.connect(self.on_text_analysis_complete)
        self.current_worker.error.connect(lambda e: self.on_error(e))
        self.current_worker.start()
    
    def on_text_analysis_complete(self, result: dict):
        """Обработка результата анализа текста"""
        self.hide_loading()
        
        if result.get("success") and result.get("analysis"):
            self.show_results(result["analysis"], "text")
        else:
            self.show_error(result.get("error", "Неизвестная ошибка"))
    
    def analyze_image(self):
        """Анализ изображения"""
        if not self.drop_zone.selected_file:
            self.show_error("Выберите изображение для анализа")
            return
        
        self.show_loading("Анализирую изображение...")
        
        self.current_worker = WorkerThread(api_client.analyze_image, self.drop_zone.selected_file)
        self.current_worker.finished.connect(self.on_image_analysis_complete)
        self.current_worker.error.connect(lambda e: self.on_error(e))
        self.current_worker.start()
    
    def on_image_analysis_complete(self, result: dict):
        """Обработка результата анализа изображения"""
        self.hide_loading()
        
        if result.get("success") and result.get("analysis"):
            self.show_results(result["analysis"], "image")
        else:
            self.show_error(result.get("error", "Неизвестная ошибка"))
    
    def parse_site(self):
        """Парсинг сайта"""
        url = self.url_input.text().strip()
        
        if not url:
            self.show_error("Введите URL сайта")
            return
        
        self.show_loading("Загружаю и анализирую сайт...")
        
        self.current_worker = WorkerThread(api_client.parse_demo, url)
        self.current_worker.finished.connect(self.on_parse_complete)
        self.current_worker.error.connect(lambda e: self.on_error(e))
        self.current_worker.start()
    
    def on_parse_complete(self, result: dict):
        """Обработка результата парсинга"""
        self.hide_loading()
        
        if result.get("success") and result.get("data"):
            data = result["data"]
            if data.get("analysis"):
                self.show_results(data["analysis"], "parse")
            else:
                self.show_error("Не удалось проанализировать сайт")
        else:
            self.show_error(result.get("error", "Неизвестная ошибка"))
    
    def load_history(self):
        """Загрузка истории"""
        result = api_client.get_history()
        
        # Очищаем
        while self.history_layout.count():
            child = self.history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if result.get("items"):
            for item in result["items"]:
                frame = QFrame()
                frame.setObjectName("historyItem")
                layout = QHBoxLayout(frame)
                
                # Иконка
                icons = {"text": "📝", "image": "🖼️", "parse": "🌐"}
                icon = QLabel(icons.get(item.get("request_type", ""), "📄"))
                icon.setStyleSheet("font-size: 24px;")
                
                # Контент
                content = QWidget()
                content_layout = QVBoxLayout(content)
                content_layout.setContentsMargins(0, 0, 0, 0)
                
                type_labels = {"text": "Анализ текста", "image": "Анализ изображения", "parse": "Парсинг сайта"}
                type_label = QLabel(type_labels.get(item.get("request_type", ""), item.get("request_type", "")))
                type_label.setStyleSheet("color: #22d3ee; font-size: 12px; font-weight: bold;")
                
                summary = QLabel(item.get("request_summary", "")[:60] + "...")
                summary.setStyleSheet("color: #94a3b8;")
                
                content_layout.addWidget(type_label)
                content_layout.addWidget(summary)
                
                # Время
                timestamp = item.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        time_str = dt.strftime("%d.%m %H:%M")
                    except:
                        time_str = timestamp[:16]
                else:
                    time_str = ""
                
                time_label = QLabel(time_str)
                time_label.setStyleSheet("color: #64748b; font-size: 12px;")
                
                layout.addWidget(icon)
                layout.addWidget(content, stretch=1)
                layout.addWidget(time_label)
                
                self.history_layout.addWidget(frame)
        else:
            empty_label = QLabel("📋 История пуста")
            empty_label.setStyleSheet("color: #64748b; font-size: 16px; padding: 40px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_layout.addWidget(empty_label)
        
        self.history_layout.addStretch()
    
    def clear_history(self):
        """Очистка истории"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите очистить историю?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            api_client.clear_history()
            self.load_history()
    
    def on_error(self, error: str):
        """Обработка ошибки"""
        self.hide_loading()
        self.show_error(error)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

```

```python
"""
Скрипт сборки .exe файла для Windows
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def build_exe():
    """Собрать .exe файл"""
    print("=" * 60)
    print("🔨 СБОРКА DESKTOP ПРИЛОЖЕНИЯ")
    print("=" * 60)
    
    # Текущая директория
    current_dir = Path(__file__).parent
    
    # Проверяем наличие PyInstaller
    print("\n📦 Проверка PyInstaller...")
    try:
        import PyInstaller
        print(f"   ✓ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("   ✗ PyInstaller не установлен")
        print("   Установка: pip install pyinstaller")
        sys.exit(1)
    
    # Имя приложения
    app_name = "CompetitorMonitor"
    
    # Параметры PyInstaller
    pyinstaller_args = [
        "pyinstaller",
        "--name", app_name,
        "--onefile",           # Один .exe файл
        "--windowed",          # Без консоли
        "--noconfirm",         # Перезаписывать без подтверждения
        "--clean",             # Очистить кеш
        
        # Иконка (если есть)
        # "--icon", "icon.ico",
        
        # Добавляем файлы
        "--add-data", f"styles.py{os.pathsep}.",
        "--add-data", f"api_client.py{os.pathsep}.",
        
        # Скрытые импорты
        "--hidden-import", "PyQt6",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "requests",
        
        # Главный файл
        "main.py"
    ]
    
    print(f"\n🚀 Запуск сборки: {app_name}.exe")
    print("-" * 60)
    
    # Запускаем PyInstaller
    result = subprocess.run(pyinstaller_args, cwd=current_dir)
    
    if result.returncode == 0:
        exe_path = current_dir / "dist" / f"{app_name}.exe"
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("\n" + "=" * 60)
            print("✅ СБОРКА ЗАВЕРШЕНА УСПЕШНО!")
            print("=" * 60)
            print(f"\n📁 Файл: {exe_path}")
            print(f"📊 Размер: {size_mb:.1f} MB")
            print("\n💡 Для запуска:")
            print(f"   1. Запустите backend: python run.py")
            print(f"   2. Запустите {app_name}.exe")
        else:
            print("\n❌ Ошибка: .exe файл не найден")
    else:
        print("\n❌ Ошибка сборки")
        sys.exit(1)


def clean():
    """Очистить артефакты сборки"""
    current_dir = Path(__file__).parent
    
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = ["*.spec"]
    
    print("🧹 Очистка артефактов сборки...")
    
    for dir_name in dirs_to_remove:
        dir_path = current_dir / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"   Удалено: {dir_name}/")
    
    for pattern in files_to_remove:
        for file in current_dir.glob(pattern):
            file.unlink()
            print(f"   Удалено: {file.name}")
    
    print("✓ Очистка завершена")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean()
    else:
        build_exe()

```

```markdown
# 🖥️ Мониторинг конкурентов - Desktop App

Десктопное приложение на PyQt6, полностью повторяющее функционал веб-интерфейса.

## 📋 Требования

- Python 3.9+
- Запущенный backend сервер (из корневой директории проекта)

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd desktop
pip install -r requirements.txt
```

### 2. Запуск приложения

**Важно:** Сначала запустите backend сервер!

```bash
# В корне проекта:
python run.py

# В отдельном терминале, в папке desktop:
cd desktop
python main.py
```

## 📦 Сборка .exe

### Сборка исполняемого файла

```bash
cd desktop
python build.py
```

После сборки файл `CompetitorMonitor.exe` будет в папке `dist/`.

### Очистка артефактов сборки

```bash
python build.py clean
```

## 🎨 Функционал

- **📝 Анализ текста** — вставьте текст конкурента для анализа
- **🖼️ Анализ изображений** — drag & drop изображений
- **🌐 Парсинг сайта** — введите URL для автоматического анализа
- **📋 История** — просмотр последних 10 запросов

## 🔧 Архитектура

```
desktop/
├── main.py          # Главное окно PyQt6
├── styles.py        # Тёмная тема с cyan акцентами
├── api_client.py    # HTTP клиент для backend API
├── build.py         # Скрипт сборки .exe
├── requirements.txt # Зависимости
└── README.md        # Этот файл
```

## ⚠️ Важно

- Приложение требует запущенный backend на `http://localhost:8000`
- При сборке .exe backend должен быть запущен отдельно
- Для полностью автономного приложения нужно встроить backend (не реализовано)

## 🖼️ Скриншот

Интерфейс повторяет веб-версию:
- Тёмная тема
- Боковая панель навигации
- Карточки с формами ввода
- Результаты анализа в красивых блоках

```

Готово! Создал десктопное приложение на PyQt6 в папке `desktop/`.

## 📁 Структура

```
desktop/
├── main.py          # Главное окно PyQt6 (500+ строк)
├── styles.py        # Тёмная тема с cyan акцентами
├── api_client.py    # HTTP клиент для backend
├── build.py         # Скрипт сборки .exe
├── requirements.txt # Зависимости
└── README.md        # Документация
```

## 🚀 Запуск

### 1. Установите зависимости:

```powershell
cd desktop
pip install -r requirements.txt
```

### 2. Запустите backend (в отдельном терминале):

```powershell
cd ..
python run.py
```

### 3. Запустите desktop приложение:

```powershell
cd desktop
python main.py
```

## 📦 Сборка в .exe

```powershell
cd desktop
python build.py
```

После сборки файл `CompetitorMonitor.exe` появится в папке `desktop/dist/`.

## 🎨 Возможности приложения

- **📝 Анализ текста** — поле ввода с placeholder
- **🖼️ Анализ изображений** — drag & drop зона с превью
- **🌐 Парсинг сайта** — поле URL с автодополнением https://
- **📋 История** — список последних запросов
- **Тёмная тема** — идентичная веб-версии
- **Индикатор статуса** — показывает подключение к серверу

```plaintext
desktop/
├── main.py          # Главное окно PyQt6 (500+ строк)
├── styles.py        # Тёмная тема с cyan акцентами
├── api_client.py    # HTTP клиент для backend
├── build.py         # Скрипт сборки .exe
├── requirements.txt # Зависимости
└── README.md        # Документация
```

```powershell
cd desktop
pip install -r requirements.txt
```

```powershell
cd ..
python run.py
```

```powershell
cd desktop
python main.py
```

```powershell
cd desktop
python build.py
```

