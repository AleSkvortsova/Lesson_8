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
    target_audience: List[str] = Field(default_factory=list, description="Сегменты целевой аудитории")
    hotel_services: List[str] = Field(default_factory=list, description="Ключевые услуги и удобства отеля")
    trust_signals: List[str] = Field(default_factory=list, description="Сигналы доверия для гостя")
    guest_experience_risks: List[str] = Field(default_factory=list, description="Риски клиентского опыта")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")
    summary: str = Field("", description="Общее резюме")


class ImageAnalysis(BaseModel):
    """Анализ изображения"""
    description: str = Field("", description="Описание изображения")
    marketing_insights: List[str] = Field(default_factory=list, description="Маркетинговые инсайты")
    detected_scene_type: str = Field("", description="Тип сцены в гостиничном контексте")
    hospitality_elements: List[str] = Field(default_factory=list, description="Замеченные элементы гостиничного сервиса")
    conversion_triggers: List[str] = Field(default_factory=list, description="Триггеры конверсии к бронированию")
    visual_style_score: int = Field(0, ge=0, le=10, description="Оценка визуального стиля (0-10)")
    ux_clarity_score: int = Field(0, ge=0, le=10, description="Понятность UX и призывов к действию")
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


class CompetitorCollectionItem(BaseModel):
    """Собранные данные по одному сайту конкурента"""
    url: str
    title: Optional[str] = None
    h1: Optional[str] = None
    first_paragraph: Optional[str] = None
    screenshot_base64: Optional[str] = None
    error: Optional[str] = None


class CollectCompetitorsResponse(BaseModel):
    """Ответ ручного автосбора сайтов конкурентов"""
    success: bool
    items: List[CompetitorCollectionItem] = Field(default_factory=list)
    total: int = 0
    successful: int = 0
    failed: int = 0
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

