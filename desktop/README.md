# Desktop App (PyQt6 + PyInstaller)

Desktop-клиент повторяет функционал веб-интерфейса:
- анализ текста;
- анализ изображения;
- парсинг и анализ сайта;
- ручной сбор конкурентов (`/collect_competitors`);
- просмотр и очистка истории.

## Установка

```bash
python -m pip install -r desktop/requirements.txt
```

## Запуск в режиме разработки

```bash
python desktop/app.py
```

По умолчанию клиент обращается к `http://127.0.0.1:8000`.  
Можно переопределить через переменную:

```bash
set DESKTOP_API_BASE_URL=http://127.0.0.1:8000
```

## Сборка `.exe` (Windows)

```bash
python desktop/build.py
```

Результат сборки: `dist/CompetitorMonitorDesktop.exe`.
