# Анализ приложения Investing Demo

Этот раздел фиксирует анализ исходного состояния проекта для задания 1. Все выводы сопровождаются ссылками на исходные файлы и строки. Последующие задания добавляются в отдельные разделы ниже и не заменяют этот анализ.

## 1. Назначение приложения и технологический стек

Investing Demo — веб-приложение-каталог акций: пользователь просматривает список и карточку инструмента, а авторизованный пользователь может создавать, редактировать и удалять записи. Приложение также содержит REST API, регистрацию/вход, загрузку котировок через Tinkoff Invest API и фоновое обновление цены. Это подтверждается маршрутами HTML и API в [`dashboard/urls.py`](./dashboard/urls.py#L11-L19), представлениями каталога [`dashboard/views.py`](./dashboard/views.py#L20-L63), API ViewSet [`dashboard/api/v1/views.py`](./dashboard/api/v1/views.py#L10-L22) и фоновой задачей [`dashboard/tasks.py`](./dashboard/tasks.py#L7-L28).

В `manage.py` указан стандартный Django entry point, а настройки проекта и подключённые приложения находятся в `config/settings.py`: [`manage.py`](./manage.py#L1-L22), [`config/settings.py`](./config/settings.py#L13-L35). Конкретные версии библиотек приведены в разделе 4 по исходному [`requirements.txt`](./requirements.txt#L1-L40).

## 2. Структура проекта

- **`config/`** — настройки Django, корневая маршрутизация и конфигурация Celery: [`config/settings.py`](./config/settings.py#L1-L35), [`config/urls.py`](./config/urls.py#L1-L8), [`config/celery.py`](./config/celery.py#L1-L18).
- **`dashboard/`** — прикладная область каталога акций: модель, формы, HTML-представления, REST API, сервисы и Celery-задача: [`dashboard/models.py`](./dashboard/models.py#L1-L21), [`dashboard/forms.py`](./dashboard/forms.py#L1-L11), [`dashboard/views.py`](./dashboard/views.py#L1-L63), [`dashboard/tasks.py`](./dashboard/tasks.py#L1-L28).
- **`dashboard/api/`** — версии и маршрутизация REST API; реализация v1 расположена в `dashboard/api/v1/`: [`dashboard/api/urls.py`](./dashboard/api/urls.py#L1-L5), [`dashboard/api/v1/urls.py`](./dashboard/api/v1/urls.py#L1-L5), [`dashboard/api/v1/router.py`](./dashboard/api/v1/router.py#L1-L6).
- **`dashboard/services/`** — внешние рыночные данные и подготовка графика: [`dashboard/services/market_data.py`](./dashboard/services/market_data.py#L1-L11), [`dashboard/services/graph.py`](./dashboard/services/graph.py#L1-L36).
- **`dashboard/management/commands/`** — пользовательские Django management-команды; исходная команда загрузки списка инструментов — `add_shares.py`: [`dashboard/management/commands/add_shares.py`](./dashboard/management/commands/add_shares.py#L1-L24).
- **`dashboard/migrations/`** — версии схемы базы данных для модели `Share`: [`dashboard/migrations/0001_add_share.py`](./dashboard/migrations/0001_add_share.py#L1-L30), [`dashboard/migrations/0007_add_updated_at.py`](./dashboard/migrations/0007_add_updated_at.py#L1-L17).
- **`dashboard/templates/dashboard/`** — страницы каталога и карточки; например, список акций выводит таблицу и ссылки на действия: [`dashboard/templates/dashboard/list.html`](./dashboard/templates/dashboard/list.html#L7-L50), [`dashboard/templates/dashboard/detail.html`](./dashboard/templates/dashboard/detail.html#L7-L28).
- **`dashboard/static/dashboard/`** — CSS-файлы интерфейса, подключаемые базовым шаблоном: [`dashboard/templates/dashboard/base.html`](./dashboard/templates/dashboard/base.html#L1-L16).
- **`user/`** — формы, представления и шаблоны регистрации, входа и выхода: [`user/urls.py`](./user/urls.py#L1-L11), [`user/views.py`](./user/views.py#L1-L64), [`user/forms.py`](./user/forms.py#L1-L70).
- **Корневые файлы**: `manage.py` запускает Django-команды; `requirements.txt` фиксирует Python-зависимости; `docker-compose.yml` описывает PostgreSQL и Redis: [`manage.py`](./manage.py#L7-L22), [`requirements.txt`](./requirements.txt#L1-L40), [`docker-compose.yml`](./docker-compose.yml#L1-L19).

## 3. Архитектура и взаимодействие компонентов

### HTML-запросы

Корневой роутер отправляет `/admin/` в Django Admin, `/` в `dashboard.urls`, а префикс `user` — в `user.urls`: [`config/urls.py`](./config/urls.py#L4-L8). В `dashboard.urls` определены список, карточка акции, создание, редактирование и удаление; там же подключён API: [`dashboard/urls.py`](./dashboard/urls.py#L11-L19).

Для списка `ShareListView` выбирает модель `Share`, шаблон списка, сортировку по названию и пагинацию по 100 записей. Детальное представление получает акцию по ID и передаёт объект вместе с результатом `get_graph()` в шаблон карточки. Create/Update/Delete используют `ShareModelForm` и после успешной операции возвращают пользователя к списку. Эти связи видны в [`dashboard/views.py`](./dashboard/views.py#L20-L63), [`dashboard/forms.py`](./dashboard/forms.py#L6-L11) и [`dashboard/templates/dashboard/detail.html`](./dashboard/templates/dashboard/detail.html#L7-L28).

### REST API

Маршрут `/api/` из dashboard подключает `dashboard.api.urls`, далее `/v1/` включает URL router v1, а `DefaultRouter` регистрирует `ShareViewSet` на `shares`: [`dashboard/urls.py`](./dashboard/urls.py#L19), [`dashboard/api/urls.py`](./dashboard/api/urls.py#L1-L5), [`dashboard/api/v1/urls.py`](./dashboard/api/v1/urls.py#L1-L5), [`dashboard/api/v1/router.py`](./dashboard/api/v1/router.py#L1-L6).

`ShareViewSet` использует `ModelViewSet`, queryset `Share.objects.all()` и `ShareSerializer`; фильтрация задаётся по `name` и `ticker`, сортировка разрешена по тем же полям, поиск настроен по имени. Сериализатор перечисляет поля, отдаваемые API: [`dashboard/api/v1/views.py`](./dashboard/api/v1/views.py#L10-L22), [`dashboard/api/v1/serializer.py`](./dashboard/api/v1/serializer.py#L6-L19). Настройки DRF задают pagination limit-offset с размером страницы 100 и backend для django-filter: [`config/settings.py`](./config/settings.py#L31-L35).

### Пользователи, Celery и сервисы

`user.urls` направляет запросы авторизации, регистрации и выхода в соответствующие Django views. Представления вызывают `authenticate`, `login` и `logout`; регистрационная форма проверяет данные и создаёт пользователя: [`user/urls.py`](./user/urls.py#L7-L11), [`user/views.py`](./user/views.py#L8-L64), [`user/forms.py`](./user/forms.py#L8-L53). Операции HTML по созданию, изменению и удалению акций защищены mixin-проверкой `request.user.is_authenticated`: [`dashboard/views.py`](./dashboard/views.py#L11-L17), [`dashboard/views.py`](./dashboard/views.py#L41-L63).

`config/celery.py` создаёт Celery app, загружает настройки Django, обнаруживает tasks и планирует `dashboard.tasks.update_last_price` каждые 10 секунд: [`config/celery.py`](./config/celery.py#L1-L18), [`config/settings.py`](./config/settings.py#L136-L144). Задача перебирает акции, запрашивает через `get_last_data()` цену/время и обновляет цену и флаг тренда через ORM: [`dashboard/tasks.py`](./dashboard/tasks.py#L7-L28). Сервис котировок вызывает Tinkoff `market_data.get_last_prices` по FIGI: [`dashboard/services/market_data.py`](./dashboard/services/market_data.py#L6-L11). Сервис графика запрашивает дневные свечи за 180 дней и строит Plotly scatter-график: [`dashboard/services/graph.py`](./dashboard/services/graph.py#L11-L36).

## 4. Библиотеки и внешние зависимости

Версии ниже переписаны из исходного [`requirements.txt`](./requirements.txt#L1-L40). Это закреплённые версии зависимостей репозитория; наличие версии в файле само по себе не означает, что каждая библиотека напрямую импортируется приложением.

| Пакет | Версия |
|---|---:|
| amqp | 5.1.1 |
| asgiref | 3.6.0 |
| async-timeout | 4.0.2 |
| billiard | 3.6.4.0 |
| black | 23.1.0 |
| cachetools | 5.3.0 |
| celery | 5.2.7 |
| click | 8.1.3 |
| click-didyoumean | 0.3.0 |
| click-plugins | 1.1.1 |
| click-repl | 0.2.0 |
| crispy-bootstrap3 | 2022.1 |
| Django | 4.1.7 |
| django-crispy-forms | 2.0 |
| django-filter | 22.1 |
| djangorestframework | 3.14.0 |
| grpcio | 1.51.3 |
| isort | 5.12.0 |
| kombu | 5.2.4 |
| mypy-extensions | 1.0.0 |
| packaging | 23.0 |
| pathspec | 0.11.1 |
| platformdirs | 3.1.1 |
| plotly | 5.13.1 |
| prompt-toolkit | 3.0.38 |
| protobuf | 3.20.3 |
| psycopg2-binary | 2.9.5 |
| pydantic | 1.10.6 |
| python-dateutil | 2.8.2 |
| pytz | 2022.7.1 |
| redis | 4.5.1 |
| six | 1.16.0 |
| sqlparse | 0.4.3 |
| tenacity | 8.2.2 |
| tinkoff | 0.1.1 |
| tinkoff-investments | 0.2.0b50 |
| tomli | 2.0.1 |
| typing_extensions | 4.5.0 |
| vine | 5.0.0 |
| wcwidth | 0.2.6 |

Основные используемые группы: Django и DRF для web/API (установленные приложения перечислены в [`config/settings.py`](./config/settings.py#L13-L26)); Celery, Kombu/AMQP и Redis для фоновой очереди и брокера ([`config/celery.py`](./config/celery.py#L1-L18), [`config/settings.py`](./config/settings.py#L136-L144)); Plotly для графика ([`dashboard/services/graph.py`](./dashboard/services/graph.py#L3-L4)); Tinkoff SDK для рыночных цен и свечей ([`dashboard/services/market_data.py`](./dashboard/services/market_data.py#L1-L11), [`dashboard/services/graph.py`](./dashboard/services/graph.py#L5-L17)); PostgreSQL driver соответствует database backend из настроек и Docker-сервису ([`config/settings.py`](./config/settings.py#L91-L104), [`docker-compose.yml`](./docker-compose.yml#L3-L14)).

## 5. Модель данных исходной версии

Основная прикладная сущность — `Share`, объявленная в [`dashboard/models.py`](./dashboard/models.py#L4-L21):

| Поле | Тип и ограничения |
|---|---|
| `figi` | `CharField(255)`, уникальный |
| `isin` | `CharField(255)` |
| `name` | `CharField(255)`, verbose name «Наименование компании» |
| `ticker` | `CharField(10)`, уникальный |
| `currency` | `CharField(20)` |
| `uid` | `CharField(255)`, уникальный |
| `last_price` | nullable/blank `FloatField` |
| `is_trend_high` | nullable/blank `BooleanField` |
| `updated_at` | `DateTimeField(auto_now=True)`, nullable/blank |

В модели `Share` нет внешних ключей и связей с пользователями. Пользовательская сущность — встроенная Django user model: `user/models.py` получает её через `get_user_model()`, а миграции приложения не объявляют отдельную пользовательскую таблицу ([`user/models.py`](./user/models.py#L1-L3), [`dashboard/models.py`](./dashboard/models.py#L4-L21)). История изменения модели `Share` хранится в `dashboard/migrations/`: [`dashboard/migrations/0001_add_share.py`](./dashboard/migrations/0001_add_share.py#L1-L30), [`dashboard/migrations/0007_add_updated_at.py`](./dashboard/migrations/0007_add_updated_at.py#L1-L17).

## 6. Обработка запросов и взаимодействие с базой данных

По умолчанию в исходных настройках Django подключается PostgreSQL `investing` на `localhost:5432` с пользователем `postgres`; ORM использует базу через настройки `DATABASES`: [`config/settings.py`](./config/settings.py#L91-L104). Схема создаётся последовательностью миграций dashboard: [`dashboard/migrations/0001_add_share.py`](./dashboard/migrations/0001_add_share.py#L1-L30), [`dashboard/migrations/0007_add_updated_at.py`](./dashboard/migrations/0007_add_updated_at.py#L1-L17).

Основные пути обработки:

1. **Каталог:** GET `/` → `config.urls` → `dashboard.urls` → `ShareListView` → Django ORM по `Share` → `dashboard/list.html`. `ShareListView` сортирует по `name` и выдаёт до 100 строк на страницу: [`config/urls.py`](./config/urls.py#L4-L8), [`dashboard/urls.py`](./dashboard/urls.py#L13-L19), [`dashboard/views.py`](./dashboard/views.py#L20-L27), [`dashboard/templates/dashboard/list.html`](./dashboard/templates/dashboard/list.html#L15-L40).
2. **Карточка:** GET `/<id>` → `ShareDetailView` получает запись из ORM, вызывает графический сервис и передаёт `share`/`plot_div` в detail template: [`dashboard/urls.py`](./dashboard/urls.py#L13-L16), [`dashboard/views.py`](./dashboard/views.py#L29-L39), [`dashboard/templates/dashboard/detail.html`](./dashboard/templates/dashboard/detail.html#L7-L28).
3. **Управление каталогом:** create/update/delete URL → generic Django view → `ShareModelForm` → ORM save/delete → перенаправление на список; доступ ограничен проверкой авторизации: [`dashboard/urls.py`](./dashboard/urls.py#L16-L18), [`dashboard/views.py`](./dashboard/views.py#L11-L17), [`dashboard/views.py`](./dashboard/views.py#L41-L63), [`dashboard/forms.py`](./dashboard/forms.py#L6-L11).
4. **API:** `/api/v1/shares/` → router → `ShareViewSet` → queryset/ORM → фильтрация, сортировка и сериализация `ShareSerializer` в JSON: [`dashboard/api/urls.py`](./dashboard/api/urls.py#L3-L5), [`dashboard/api/v1/router.py`](./dashboard/api/v1/router.py#L5-L6), [`dashboard/api/v1/views.py`](./dashboard/api/v1/views.py#L16-L22), [`dashboard/api/v1/serializer.py`](./dashboard/api/v1/serializer.py#L6-L19).
5. **Аутентификация:** `/user/login/`, `/user/registration/`, `/user/logout/` → соответствующие views/forms → Django auth backend и user model: [`config/urls.py`](./config/urls.py#L4-L8), [`user/urls.py`](./user/urls.py#L7-L11), [`user/views.py`](./user/views.py#L8-L64), [`user/forms.py`](./user/forms.py#L8-L53).
6. **Обновление рынка:** Celery Beat запускает task; task загружает `Share` через ORM, получает данные из Tinkoff-сервиса и сохраняет новую цену/тренд через ORM `update()`: [`config/celery.py`](./config/celery.py#L13-L18), [`dashboard/tasks.py`](./dashboard/tasks.py#L7-L28), [`dashboard/services/market_data.py`](./dashboard/services/market_data.py#L6-L11).

## Дополнения по последующим заданиям

Результаты задания 2 и новые функциональные требования задания 4 добавляются отдельными разделами ниже. Исходные выводы этого раздела и анализа пунктов 1–6 не удаляются и не заменяются.
