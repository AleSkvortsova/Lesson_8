# 🔍 Мониторинг конкурентов в гостиничной сфере

MVP-приложение для конкурентного анализа отелей, апарт-отелей, хостелов и гостевых домов.  
Поддерживает анализ текста, изображений и сайтов с помощью FastAPI + ProxyAPI (OpenAI-совместимый API).

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Selenium](https://img.shields.io/badge/Selenium-Chrome-orange.svg)
![AI](https://img.shields.io/badge/AI-GPT--4o--mini-purple.svg)

## 📋 Что умеет приложение

- **Анализ текста конкурентов** с учетом гостиничной специфики
- **Анализ изображений** (номера, лобби, баннеры, интерфейсы бронирования)
- **Парсинг и AI-анализ сайта** по URL (Selenium + скриншот)
- **Автосбор сайтов конкурентов** из списка URL в `.env` при старте сервера
- **Ручной запуск автосбора** через API без перезапуска
- **История запросов** (последние 10 записей)

## 🚀 Быстрый старт

### 1) Установка зависимостей

```bash
# из корня проекта
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

python -m pip install -r requirements.txt
```

### 2) Настройка `.env`

Создайте файл `.env` в корне проекта (можно взять за основу `env.example.txt`):

```env
# ProxyAPI (OpenAI-совместимый)
PROXY_API_KEY=your_proxy_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o-mini

# Автосбор конкурентов через Selenium
COMPETITOR_URLS=https://hotel-one.com,https://hotel-two.com
AUTO_COLLECT_COMPETITORS_ON_STARTUP=true
```

### 3) Запуск сервера

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

После запуска:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 🧠 Структура AI-анализа

### Текст и сайт (`CompetitorAnalysis`)

Возвращаются поля:
- `strengths`
- `weaknesses`
- `unique_offers`
- `target_audience`
- `hotel_services`
- `trust_signals`
- `guest_experience_risks`
- `recommendations`
- `summary`

### Изображение (`ImageAnalysis`)

Возвращаются поля:
- `description`
- `marketing_insights`
- `detected_scene_type`
- `hospitality_elements`
- `conversion_triggers`
- `visual_style_score` (0-10)
- `ux_clarity_score` (0-10)
- `visual_style_analysis`
- `recommendations`

## 🌐 API эндпоинты

- `POST /analyze_text` — анализ текста конкурента
- `POST /analyze_image` — анализ изображения
- `POST /parse_demo` — парсинг одного сайта + AI-анализ
- `POST /collect_competitors` — ручной запуск автосбора сайтов конкурентов из `COMPETITOR_URLS`
- `GET /history` — получить историю
- `DELETE /history` — очистить историю
- `GET /health` — healthcheck

## 🤖 Автосбор конкурентов (Selenium)

`ParserService` использует headless Chrome и:
- открывает каждый URL из `COMPETITOR_URLS`
- извлекает `title`, `h1`, первый информативный абзац
- делает скриншот страницы
- конвертирует скриншот в Base64 для дальнейшего AI-анализа

### Режимы запуска

- **Автоматически при старте**: `AUTO_COLLECT_COMPETITORS_ON_STARTUP=true`
- **Вручную через API**: `POST /collect_competitors`

## 📁 Структура проекта

```text
backend/
  main.py                  # FastAPI приложение и эндпоинты
  config.py                # Настройки и переменные окружения
  models/schemas.py        # Pydantic-схемы запросов/ответов
  services/
    openai_service.py      # AI-анализ (текст/изображение/сайт)
    parser_service.py      # Selenium-парсинг и автосбор конкурентов
    history_service.py     # История запросов
frontend/
  index.html
  app.js
  styles.css
```

## 🛠️ Стек

- **Backend**: FastAPI, Pydantic, Uvicorn
- **AI**: ProxyAPI (OpenAI-совместимый), GPT-4o-mini
- **Парсинг**: Selenium, webdriver-manager
- **Frontend**: Vanilla JS, CSS3

## ⚠️ Требования

- Python 3.9+
- Установленный браузер Google Chrome
- Интернет-соединение для Selenium и AI-запросов
- Ключ `PROXY_API_KEY`

## 📝 Лицензия

MIT License

