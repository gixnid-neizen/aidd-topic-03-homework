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

---

## Функциональные требования (задание 2)

Восстановлены на основе реально реализованного кода. Каждое требование ссылается на файл и функцию/класс.

### FR-1. Просмотр списка акций
Пользователь (включая неавторизованного) открывает главную страницу и видит пагинированный список акций с тикером, названием, ISIN, текущей ценой и валютой.
Подтверждение: dashboard/views.py ShareListView (стр. 20–26), dashboard/urls.py (стр. 14), шаблон dashboard/templates/dashboard/list.html (стр. 15–85).

### FR-2. Просмотр детальной информации об акции с графиком
Пользователь переходит на страницу акции и видит название, цену, валюту, время обновления и исторический график.
Подтверждение: dashboard/views.py ShareDetailView.get (стр. 29–38), dashboard/services/graph.py get_graph (стр. 11–35), шаблон detail.html.

### FR-3. Создание акции (только авторизованный)
Авторизованный пользователь заполняет форму и создаёт новую акцию.
Подтверждение: dashboard/views.py ShareCreateView (стр. 41–46), IsUserAuthenticatedMixin (стр. 11–17), dashboard/forms.py ShareModelForm (стр. 6–11), шаблон create.html.

### FR-4. Редактирование акции (только авторизованный)
Авторизованный пользователь редактирует существующую акцию.
Подтверждение: dashboard/views.py ShareUpdateView (стр. 49–55).

### FR-5. Удаление акции (только авторизованный)
Авторизованный пользователь подтверждает удаление акции.
Подтверждение: dashboard/views.py ShareDeleteView (стр. 58–63), шаблон delete.html.

### FR-6. Регистрация пользователя
Пользователь регистрируется по e-mail и паролю (с подтверждением пароля), после чего автоматически авторизуется.
Подтверждение: user/views.py RegistrationView (стр. 36–55), user/forms.py RegistrationForm (стр. 8–53), user/urls.py (стр. 9).

### FR-7. Авторизация пользователя
Пользователь входит по e-mail и паролю и перенаправляется на главную.
Подтверждение: user/views.py AuthView (стр. 8–33), user/forms.py AuthForm (стр. 56–70), user/urls.py (стр. 8).

### FR-8. Выход пользователя
Авторизованный пользователь может выйти из системы.
Подтверждение: user/views.py LogoutView (стр. 58–64), user/urls.py (стр. 10).

### FR-9. REST API: получение списка акций
GET /api/v1/shares/ возвращает пагинированный список акций.
Подтверждение: dashboard/api/v1/views.py ShareViewSet (стр. 16–20), dashboard/api/v1/router.py (стр. 5–6).

### FR-10. REST API: получение, создание, обновление, удаление одной акции
GET/PUT/DELETE /api/v1/shares/<id>/ поддерживают CRUD над отдельной акцией.
Подтверждение: dashboard/api/v1/views.py ShareViewSet (ModelViewSet).

### FR-11. REST API: фильтрация и поиск
Акции можно фильтровать по name, ticker, искать по имени, сортировать по name, ticker.
Подтверждение: dashboard/api/v1/views.py ShareFilter (стр. 10–13), filter_backends, ordering_fields, search_fields (стр. 16–21).

### FR-12. Фоновое обновление цен
Celery-задача периодически обновляет last_price и is_trend_high для всех акций через Tinkoff API.
Подтверждение: dashboard/tasks.py update_last_price (стр. 7–28), config/celery.py beat_schedule (стр. 13–17), dashboard/services/market_data.py get_last_data (стр. 6–10).

### FR-13. Защита создания/редактирования/удаления акций от неавторизованного доступа
Создание, редактирование и удаление акций доступны только авторизованным пользователям.
Подтверждение: dashboard/views.py IsUserAuthenticatedMixin.test_func (стр. 12–13), применяется в ShareCreateView/ShareUpdateView/ShareDeleteView.

### Бизнес-правила и ограничения
- figi и ticker уникальны (dashboard/migrations/0002_update_share.py).
- uid уникален (dashboard/migrations/0003_add_uuid.py).
- Пароли при регистрации должны совпадать; e-mail не должен дублироваться (user/forms.py RegistrationForm.clean, стр. 30–46).
- CSRF-токен обязателен в формах ({% csrf_token %} во всех шаблонах форм).
- SECRET_KEY = "" — пустой ключ в config/settings.py (стр. 6), что мешает работе Django в современных версиях.

### Неоднозначности и возможные дефекты (не являются требованиями)
1. ShareDetailView.get использует Share.objects.get(id=pk) — при отсутствии акции вернётся 500 вместо 404 (dashboard/views.py, стр. 32).
2. list.html имеет непарные теги <td> при отрисовке цвета цены (стр. 35–40), нарушена вёрстка.
3. Внешний API Tinkoff требует токена (TINKOFF_TOKEN = "", settings.py стр. 134) — детальная страница и задачи упадут без токена.
4. База данных настроена на PostgreSQL, который может не быть доступен в среде запуска.
5. Миграция 0004_add_last_price.py содержит опечатку verbose_name="Ти" для ticker (стр. 37) и некорректный verbose_name="Валюта" для name (стр. 32).
6. dashboard/tests.py использует APITestCase и реальные URL API; тесты HTML-страниц отсутствуют.

