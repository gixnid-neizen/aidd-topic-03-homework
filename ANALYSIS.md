# ANALYSIS.md — Инвестиционный демо-проект (Django)

## 1. Назначение приложения и технологический стек

**Назначение:** веб-приложение для учёта и мониторинга акций (инвестиционный демо-сервис). Пользователь может просматривать список акций, смотреть детальную информацию с графиком исторических цен, добавлять, редактировать и удалять акции. Есть регистрация/авторизация пользователей и REST API для работы с акциями.

**Технологический стек:**
- Python 3.14.4
- Django 4.1.7 (requirements.txt, стр. 13) — веб-фреймворк
- django-crispy-forms 2.0 + crispy-bootstrap3 — рендеринг форм
- djangorestframework 3.14.0 + django-filter 22.1 — REST API
- PostgreSQL — база данных (config/settings.py, стр. 96–103)
- Redis + Celery — фоновое обновление цен (config/celery.py, dashboard/tasks.py)
- Tinkoff Invest API — источник котировок (dashboard/services/graph.py, dashboard/services/market_data.py)
- Plotly — построение графиков (dashboard/services/graph.py)
- Bootstrap 3 (CDN + локальные CSS) — фронтенд (dashboard/templates/dashboard/base.html)

## 2. Структура проекта и назначение каталогов/файлов

Корень проекта: /home/default/projects/homework/cline

- manage.py — точка входа управления Django (DJANGO_SETTINGS_MODULE=config.settings)
- requirements.txt — зависимости проекта
- docker-compose.yml — PostgreSQL и Redis в контейнерах
- README.md — краткая инструкция по запуску
- .gitignore, .venv — виртуальное окружение

config/ — настройки проекта:
- config/settings.py — настройки Django (БД PostgreSQL, SECRET_KEY, INSTALLED_APPS, REST_FRAMEWORK, CELERY, TINKOFF_TOKEN)
- config/urls.py — корневой роутинг (/admin, dashboard, user)
- config/celery.py — конфигурация Celery, расписание update_last_price каждые 10 сек
- config/wsgi.py, config/asgi.py — WSGI/ASGI точки входа

dashboard/ — основное приложение (акции):
- dashboard/models.py — модель Share (акция)
- dashboard/views.py — представления: список, детальная страница, создание, редактирование, удаление
- dashboard/urls.py — маршруты приложения (index, detail, create, update, delete, api/)
- dashboard/forms.py — форма ShareModelForm
- dashboard/admin.py — регистрация Share в админке
- dashboard/api/ — REST API (роутер, представления, сериализатор, фильтры)
- dashboard/services/graph.py — получение свечей и построение графика через Tinkoff API + Plotly
- dashboard/services/market_data.py — получение последней цены через Tinkoff API
- dashboard/tasks.py — Celery-задача update_last_price
- dashboard/migrations/ — миграции 0001…0007 для модели Share
- dashboard/templates/dashboard/ — шаблоны base.html, list.html, create.html, detail.html, delete.html
- dashboard/static/dashboard/css/ — локальные CSS (Bootstrap, sticky-footer)
- dashboard/tests.py — тесты REST API (APITestCase)

user/ — приложение аутентификации:
- user/models.py — alias User = get_user_model()
- user/views.py — AuthView, RegistrationView, LogoutView
- user/urls.py — маршруты /login/, /registration/, /logout/
- user/forms.py — RegistrationForm, AuthForm
- user/templates/user/ — base.html, auth.html, registration.html

## 3. Архитектура и взаимодействие компонентов

Традиционная Django MVC-подобная архитектура:

1. Запрос → URL → View: config/urls.py распределяет запросы между dashboard.urls, user.urls и админкой. Каждое приложение имеет своё urls.py с app_name.
2. View → Model: представления (dashboard/views.py) используют ORM для работы с моделью Share (dashboard/models.py).
3. View → Template: рендеринг HTML-шаблонов через render() с контекстом; базовый шаблон base.html с навигацией и блоком content.
4. View → Form: создание/редактирование через ShareModelForm (forms.py) с CSRF-защитой.
5. REST API: dashboard/api/v1/views.py — ShareViewSet (ModelViewSet) с фильтрацией, поиском и сортировкой; маршрут /api/v1/shares/.
6. Фоновые задачи: Celery (config/celery.py, dashboard/tasks.py) периодически вызывает dashboard/services/market_data.py:get_last_data, который опрашивает Tinkoff API и обновляет Share.last_price / Share.is_trend_high.
7. Графики: ShareDetailView вызывает dashboard/services/graph.py:get_graph, который запрашивает свечи за 180 дней у Tinkoff API и рендерит график через Plotly.

## 4. Библиотеки и внешние зависимости с версиями

См. requirements.txt. Ключевые:
- Django==4.1.7
- django-crispy-forms==2.0, crispy-bootstrap3==2022.1
- djangorestframework==3.14.0, django-filter==22.1
- celery==5.2.7, redis==4.5.1, kombu==5.2.4, amqp==5.1.1
- psycopg2-binary==2.9.5 (PostgreSQL драйвер)
- tinkoff-investments==0.2.0b50, tinkoff==0.1.1
- plotly==5.13.1
- pytz==2022.7.1, python-dateutil==2.8.2
- Инструменты разработки: black==23.1.0, isort==5.12.0, mypy-extensions==1.0.0

## 5. Модель данных (сущности, атрибуты, связи)

Одна сущность — Share (dashboard/models.py, стр. 4–21):

| Атрибут | Тип | Описание |
|---|---|---|
| id | BigAutoField (PK) | Идентификатор |
| figi | CharField(255, unique) | FIGI инструмента |
| isin | CharField(255) | ISIN |
| name | CharField(255) | Наименование компании |
| ticker | CharField(10, unique) | Тикер |
| currency | CharField(20) | Валюта |
| uid | CharField(255, unique) | UID |
| last_price | FloatField(null, blank) | Текущая цена |
| is_trend_high | BooleanField(null, blank) | Растет цена |
| updated_at | DateTimeField(auto_now) | Время обновления |

Связей (ForeignKey/ManyToMany) нет. Приложение user использует стандартную модель Django User (через get_user_model()), связей с Share не определено.

## 6. Обработка пользовательских запросов и работа с БД

URL → View:
- GET / → ShareListView (ListView), шаблон list.html, пагинация 100, сортировка по name
- GET /<int:pk> → ShareDetailView (View.get), вызывает get_graph(share), шаблон detail.html
- GET/POST /create → ShareCreateView (CreateView), форма ShareModelForm, только для авторизованных
- GET/POST /update/<int:pk> → ShareUpdateView (UpdateView)
- GET/POST /delete/<int:pk> → ShareDeleteView (DeleteView)
- GET /api/v1/shares/ → ShareViewSet (DRF ModelViewSet)

Работа с БД: через Django ORM (Share.objects.all(), .get(id=pk), .filter().update()). Подключение к PostgreSQL (config/settings.py, стр. 96–103). Миграции в dashboard/migrations/.

