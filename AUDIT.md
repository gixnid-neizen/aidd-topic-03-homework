# AUDIT.md — Технический аудит проекта Investing Demo

## Сводная таблица проблем (по приоритетам)

| № | Приоритет | Проблема | Файл:строка | Последствие |
|---|-----------|----------|-------------|-------------|
| 1 | Критично | SECRET_KEY пустая строка | config/settings.py:6 | ImproperlyConfigured при запуске Django 5+/6+, приложение не стартует |
| 2 | Критично | Зависимости несовместимы с Python 3.14.4 (Django 4.1.7 не поддерживает Python 3.14) | requirements.txt | Приложение не устанавливается/не запускается в текущем окружении |
| 3 | Критично | База данных настроена на PostgreSQL, который может отсутствовать | config/settings.py:96–103 | Ошибка подключения к БД при запуске без запущенного PostgreSQL |
| 4 | Высокий | ShareDetailView.get использует Share.objects.get(id=pk) без get_object_or_404 | dashboard/views.py:32 | 500 ошибка при запросе несуществующей акции вместо 404 |
| 5 | Высокий | Внешний API Tinkoff требует токена, TINKOFF_TOKEN пустой | config/settings.py:134 | Детальная страница (график) и задачи обновления цен падут без токена |
| 6 | Средний | Нерабочая конфигурация REST API / мёртвые настройки | config/settings.py:31–35 | REST_FRAMEWORK объявлен, но API требует токен Tinkoff для графиков; тесты API используют реальные URL |
| 7 | Средний | Миграция 0004 содержит опечатки verbose_name | dashboard/migrations/0004_add_last_price.py:32,37 | Некорректные verbose_name (name → "Валюта", ticker → "Ти") |
| 8 | Средний | Шаблон list.html имеет нарушение вёрстки (непарные <td>) | dashboard/templates/dashboard/list.html:35–40 | Некорректный HTML при отображении цвета цены |
| 9 | Низкий | Отсутствуют тесты HTML-страниц (только API) | dashboard/tests.py | Не покрыто тестирование представлений и шаблонов |
| 10 | Низкий | dashboard/models.py у модели Share нет __str__ | dashboard/models.py | Неинформативное отображение объектов в админке/оболочке |
| 11 | Низкий | Неиспользуемые / не подключённые пакеты (django_filters, crispy, rest_framework подключены, но часть функционала мёртвая) | config/settings.py:20–25 | Лишние зависимости в окружении |

## Подробный анализ

### Устаревшие библиотеки и зависимости
requirements.txt содержит Django 4.1.7, django-crispy-forms 2.0, djangorestframework 3.14.0, celery 5.2.7 и другие версии 2022–2023 года выпуска. На момент Python 3.14.4 эти версии не гарантируют совместимость (в частности, Django 4.1.7 не поддерживает Python 3.14). Требуется обновление зависимостей и requirements.txt.

### Проблемы совместимости с современным Python и Django
- Python 3.14.4 в .venv; Django 4.1.7 из requirements.txt не поддерживает такую версию Python — импорт Django не удастся.
- pytz устарел (в современном Django функциональность перенесена в zoneinfo), tomli не нужен для Python 3.11+.
- Необходимо подобрать версии Django и зависимостей, совместимые с Python 3.14.4.

### Проблемы конфигурации (settings, миграции, приложения)
- SECRET_KEY = "" (config/settings.py:6) — Django требует непустой секретный ключ.
- DATABASES жёстко задан на PostgreSQL (config/settings.py:96–103) без fallback на SQLite.
- INSTALLED_APPS содержит rest_framework, django_filters, crispy_forms, crispy_bootstrap3 — часть не используется или требует донастройки.
- TINKOFF_TOKEN = "" (config/settings.py:134) — интеграция с Тинькофф неработоспособна без токена.
- REST_FRAMEWORK объявлен (config/settings.py:31–35), но эндпоинт /api/v1/shares/ доступен; для работы graph/detail нужен токен.
- Миграция 0004_add_last_price.py содержит опечатки в verbose_name.

### Ошибки, влияющие на работоспособность
- Share.objects.get(id=pk) в ShareDetailView (dashboard/views.py:32) бросает исключение при отсутствии объекта → HTTP 500 вместо 404. Требуется замена на get_object_or_404.
- Неатомарное переключение флага тренда в dashboard/tasks.py (при сравнении share.last_price > last_price возможны условия гонки при параллельных задачах).
