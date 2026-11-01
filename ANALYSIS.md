# Анализ приложения Investing Demo

Разделы 1–8 фиксируют исходное состояние проекта на [`commit 362510b`](https://github.com/gixnid-neizen/aidd-topic-03-homework/tree/362510b); ссылки на файлы и строки относятся к этому снимку, даже если исходники модернизированы в последующих коммитах. Результаты следующих заданий добавляются после них и не заменяют исходный анализ.

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

## 7. Задание 2 — фактически реализованные требования исходной версии

Требования ниже относятся к исходному приложению до добавления функций задания 4. Это фактическое поведение и заявленные в исходном коде сценарии; обнаруженные неисправности отдельно отмечены в разделе 8.

1. **Просмотр каталога.** Система выводит акции по названию, до 100 записей на страницу; таблица показывает тикер, название, ISIN, цену и для авторизованных пользователя элементы управления. Подтверждение: [`dashboard/views.py`](./dashboard/views.py#L20-L27), [`dashboard/templates/dashboard/list.html`](./dashboard/templates/dashboard/list.html#L15-L50).
2. **Просмотр карточки.** По ID система получает акцию, показывает сведения и передаёт график в шаблон карточки. Подтверждение: [`dashboard/urls.py`](./dashboard/urls.py#L13-L16), [`dashboard/views.py`](./dashboard/views.py#L29-L39), [`dashboard/templates/dashboard/detail.html`](./dashboard/templates/dashboard/detail.html#L7-L28).
3. **Создание акции через сайт.** Форма модели принимает все поля `Share`; авторизованное создание после сохранения возвращает на список. Подтверждение: [`dashboard/forms.py`](./dashboard/forms.py#L6-L11), [`dashboard/views.py`](./dashboard/views.py#L41-L47).
4. **Редактирование акции через сайт.** Авторизованный пользователь может изменить запись через ту же ModelForm и после сохранения вернуться к каталогу. Подтверждение: [`dashboard/views.py`](./dashboard/views.py#L49-L56).
5. **Удаление акции через сайт.** Авторизованный пользователь может удалить запись через DeleteView с шаблоном подтверждения. Подтверждение: [`dashboard/views.py`](./dashboard/views.py#L58-L63).
6. **Ограничение HTML-операций управления.** Create, update и delete используют mixin, который проверяет `request.user.is_authenticated` и перенаправляет неавторизованного пользователя на каталог. Подтверждение: [`dashboard/views.py`](./dashboard/views.py#L11-L17), [`dashboard/views.py`](./dashboard/views.py#L41-L63).
7. **Получение списка акций через API.** API сериализует перечисленные поля акции; размер страницы настроен на 100 с limit-offset pagination. Подтверждение: [`dashboard/api/v1/serializer.py`](./dashboard/api/v1/serializer.py#L6-L19), [`config/settings.py`](./config/settings.py#L31-L35).
8. **CRUD по акциям через API.** DRF ModelViewSet предоставляет стандартные действия списка, получения, создания, обновления и удаления акций. Подтверждение: [`dashboard/api/v1/views.py`](./dashboard/api/v1/views.py#L16-L22), [`dashboard/api/v1/router.py`](./dashboard/api/v1/router.py#L5-L6).
9. **Фильтрация, поиск и сортировка API.** Фильтр задаёт поля `name` и `ticker`; сортировка разрешена по тем же полям, поиск настроен по имени. Подтверждение: [`dashboard/api/v1/views.py`](./dashboard/api/v1/views.py#L10-L22).
10. **Формы пользовательских действий.** В приложении определены маршруты входа, регистрации и выхода; формы требуют email/пароль, а регистрационная форма проверяет совпадение паролей и уже зарегистрированный email. Подтверждение: [`user/urls.py`](./user/urls.py#L7-L11), [`user/forms.py`](./user/forms.py#L8-L53), [`user/forms.py`](./user/forms.py#L56-L70).
11. **Обработка попытки входа.** Представление отправляет email и пароль в Django `authenticate`, при успехе вызывает login и возвращает пользователя к списку. Подтверждение: [`user/views.py`](./user/views.py#L15-L34). В исходном коде эта ветка повреждена; это не подтверждает успешно работающий вход (см. раздел 8).
12. **Выход из аккаунта.** Представление вызывает logout и перенаправляет на список. Подтверждение: [`user/views.py`](./user/views.py#L58-L64).
13. **Получение рыночной цены.** Сервис запрашивает последние цены по FIGI через Tinkoff SDK и возвращает цену и время. Подтверждение: [`dashboard/services/market_data.py`](./dashboard/services/market_data.py#L6-L11).
14. **Фоновое обновление цены и тренда.** Периодическая задача перебирает акции, получает цену и сохраняет цену/направление тренда через ORM; ошибки логируются. Подтверждение: [`dashboard/tasks.py`](./dashboard/tasks.py#L7-L28), расписание: [`config/celery.py`](./config/celery.py#L13-L18).
15. **График цены.** При доступности SDK, токена и рыночных данных система запрашивает дневные свечи за 180 дней и формирует Plotly-график. Подтверждение: [`dashboard/services/graph.py`](./dashboard/services/graph.py#L11-L36).

### Формальный список требований

Каждое требование описывает конкретное поведение и сопровождается исходным доказательством. Успешная регистрация и аутентификация не утверждаются как работающая функциональность: соответствующие вызовы исходника повреждены и отмечены отдельно в разделе дефектов.

1. **FR-01. Просмотр каталога.** Система показывает акции, отсортированные по названию, по 100 записей на страницу; таблица отображает тикер, название, ISIN, цену и (для авторизованных) ссылки управления. Подтверждение: [`ShareListView`](./dashboard/views.py#L20-L27), [`list.html`](./dashboard/templates/dashboard/list.html#L15-L50).
2. **FR-02. Просмотр карточки.** По ID система получает акцию, выводит её данные и вставляет график. Подтверждение: [`ShareDetailView.get()`](./dashboard/views.py#L29-L39), [`detail.html`](./dashboard/templates/dashboard/detail.html#L7-L28).
3. **FR-03. Создание акции.** HTML-форма построена на всех полях модели; `CreateView` сохраняет валидную запись и перенаправляет на каталог. Подтверждение: [`ShareModelForm`](./dashboard/forms.py#L6-L11), [`ShareCreateView`](./dashboard/views.py#L41-L47).
4. **FR-04. Редактирование акции.** `UpdateView` позволяет изменить выбранную запись через модельную форму и после сохранения возвращает на каталог. Подтверждение: [`ShareUpdateView`](./dashboard/views.py#L49-L56).
5. **FR-05. Удаление акции.** `DeleteView` показывает страницу подтверждения и удаляет выбранную запись после подтверждения. Подтверждение: [`ShareDeleteView`](./dashboard/views.py#L58-L63).
6. **FR-06. Авторизация HTML-управления.** Create/Update/Delete доступны только пользователю с `is_authenticated`; для остальных mixin перенаправляет на список. Подтверждение: [`IsUserAuthenticatedMixin`](./dashboard/views.py#L11-L17), [`ShareCreateView`/`ShareUpdateView`/`ShareDeleteView`](./dashboard/views.py#L41-L63).
7. **FR-07. Получение каталога через API.** API возвращает список акций с полями сериализатора в пагинации limit-offset с размером страницы 100. Подтверждение: [`ShareViewSet`](./dashboard/api/v1/views.py#L16-L22), [`ShareSerializer`](./dashboard/api/v1/serializer.py#L6-L19), [`REST_FRAMEWORK`](./config/settings.py#L31-L35).
8. **FR-08. API CRUD.** API предоставляет стандартные операции списка, получения объекта, создания, обновления и удаления акций. Подтверждение: [`ShareViewSet`](./dashboard/api/v1/views.py#L16-L22), [`router.register()`](./dashboard/api/v1/router.py#L5-L6).
9. **FR-09. Фильтрация и сортировка API.** API фильтрует по `name`/`ticker`, сортирует по ним и настраивает поиск по имени. Подтверждение: [`ShareFilter`](./dashboard/api/v1/views.py#L10-L14), [`ShareViewSet`](./dashboard/api/v1/views.py#L16-L22).
10. **FR-10. Формы пользователя.** Система предоставляет маршруты и формы login/registration/logout; регистрационная форма валидирует email-формат, требует два пароля, проверяет их совпадение и отсутствие зарегистрированного email. Подтверждение: [`user/urls.py`](./user/urls.py#L7-L11), [`RegistrationForm`](./user/forms.py#L8-L46), [`AuthForm`](./user/forms.py#L56-L70).
11. **FR-11. Обработка входа.** В view предусмотрены вызов `authenticate`, создание сессии при успешном входе и вывод ошибки при неуспехе; фактический успешный вход исходником не обеспечен из-за повреждённой строки вызова. Подтверждение: [`AuthView.post()`](./user/views.py#L15-L34); ограничение — в разделе дефектов.
12. **FR-12. Выход.** Logout view завершает текущую сессию и перенаправляет на каталог. Подтверждение: [`LogoutView.get()`](./user/views.py#L58-L64).
13. **FR-13. CSRF для HTML POST.** Django включает CSRF middleware, а HTML-формы входа и регистрации содержат `{% csrf_token %}`. Подтверждение: [`MIDDLEWARE`](./config/settings.py#L61-L69), [`auth.html`](./user/templates/user/auth.html#L3-L4), [`registration.html`](./user/templates/user/registration.html#L4-L5).
14. **FR-14. Обновление рыночной цены.** Периодическая задача получает цену и время каждой акции через сервис, пересчитывает тренд и сохраняет цену/тренд через ORM; задача планируется Celery Beat. Подтверждение: [`update_last_price()`](./dashboard/tasks.py#L7-L28), [`beat_schedule`](./config/celery.py#L13-L18), [`get_last_data()`](./dashboard/services/market_data.py#L6-L11).
15. **FR-15. График рынка.** При наличии доступного Tinkoff API система получает дневные свечи примерно за последние 180 дней и строит линейный график. Подтверждение: [`get_graph()`](./dashboard/services/graph.py#L11-L36).

### Основные пользовательские сценарии

1. Посетитель открывает `/` → URL направляется в `ShareListView` → система показывает каталог: [`config/urls.py`](./config/urls.py#L4-L8), [`dashboard/urls.py`](./dashboard/urls.py#L13-L16).
2. Посетитель выбирает акцию → система загружает её по ID и отображает карточку с графиком: [`dashboard/urls.py`](./dashboard/urls.py#L13-L16), [`dashboard/views.py`](./dashboard/views.py#L29-L39).
3. Авторизованный пользователь открывает страницу создания/редактирования/удаления → форма или подтверждение → изменение модели → перенаправление к каталогу: [`dashboard/views.py`](./dashboard/views.py#L41-L63).
4. Посетитель может открыть страницы login/registration/logout; однако операции регистрации и входа не работают корректно из-за дефектов исходных вызовов, перечисленных ниже: [`user/urls.py`](./user/urls.py#L7-L11), [`user/forms.py`](./user/forms.py#L47-L53), [`user/views.py`](./user/views.py#L15-L24).
5. API-клиент обращается к `/api/v1/shares/` и выполняет действия DRF ViewSet; фильтрация/сортировка задаются параметрами API: [`dashboard/urls.py`](./dashboard/urls.py#L19), [`dashboard/api/urls.py`](./dashboard/api/urls.py#L3-L5), [`dashboard/api/v1/views.py`](./dashboard/api/v1/views.py#L16-L22).

### Бизнес-правила и ограничения

- FIGI, тикер и UID уникальны; тикер ограничен 10 символами: [`dashboard/models.py`](./dashboard/models.py#L7-L17).
- Поля цены и тренда допускают отсутствие значения (`NULL`): [`dashboard/models.py`](./dashboard/models.py#L13-L16).
- Форма регистрации требует email, два пароля, равенство паролей и отсутствие пользователя с таким email: [`user/forms.py`](./user/forms.py#L11-L28), [`user/forms.py`](./user/forms.py#L30-L46).
- Управление акциями через HTML защищено авторизацией; API ViewSet в исходной конфигурации отдельного ограничения доступа не объявляет: [`dashboard/views.py`](./dashboard/views.py#L11-L17), [`dashboard/api/v1/views.py`](./dashboard/api/v1/views.py#L16-L22).
- В формах входа и регистрации присутствует CSRF-токен, а `CsrfViewMiddleware` включён в список middleware: [`user/templates/user/auth.html`](./user/templates/user/auth.html#L3-L4), [`user/templates/user/registration.html`](./user/templates/user/registration.html#L4-L5), [`config/settings.py`](./config/settings.py#L61-L69).
- Запрос рыночных данных и графика зависит от Tinkoff SDK, токена и ответа внешнего API: [`dashboard/services/market_data.py`](./dashboard/services/market_data.py#L6-L11), [`dashboard/services/graph.py`](./dashboard/services/graph.py#L11-L20).

## 8. Неоднозначности, противоречия и дефекты исходной версии

Эти пункты не являются функциональными требованиями:

1. В исходных регистрационной форме и view повреждены вызовы `authenticate()`; корректная регистрация/аутентификация из этого кода не следует: [`user/forms.py`](./user/forms.py#L48-L53), [`user/views.py`](./user/views.py#L15-L24).
2. `SECRET_KEY` и `ALLOWED_HOSTS` заданы пустыми: [`config/settings.py`](./config/settings.py#L4-L10).
3. База данных жёстко настроена на PostgreSQL localhost и учётные данные из settings: [`config/settings.py`](./config/settings.py#L91-L104).
4. Пакеты закреплены старыми версиями в `requirements.txt`; исходный проект не описывает диапазон поддерживаемых версий Python: [`requirements.txt`](./requirements.txt#L1-L40), [`manage.py`](./manage.py#L1-L22).
5. Tinkoff клиент создаётся независимо от проверки наличия SDK/token; отсутствие конфигурации или ошибка API может оборвать запрос/задачу: [`dashboard/services/market_data.py`](./dashboard/services/market_data.py#L6-L11), [`dashboard/services/graph.py`](./dashboard/services/graph.py#L11-L20).
6. В detail view прямой `Share.objects.get()` не преобразует отсутствие записи в HTTP 404 явно: [`dashboard/views.py`](./dashboard/views.py#L29-L39).
7. В `update_last_price()` время котировки распаковывается, но не сохраняется; trend calculation использует широкую обработку исключений, а price/trend пишутся через queryset `update()`: [`dashboard/tasks.py`](./dashboard/tasks.py#L11-L28).
8. API ViewSet предоставляет действия записи и не задаёт permission class: [`dashboard/api/v1/views.py`](./dashboard/api/v1/views.py#L16-L22).
9. В расписании Celery задача с названием `add-every-5-min` фактически настроена на интервал 10 секунд: [`config/celery.py`](./config/celery.py#L13-L18).
10. В исходной модели нет персональных списков наблюдения, виртуальных портфелей или истории цен; исходная прикладная модель только `Share`: [`dashboard/models.py`](./dashboard/models.py#L4-L21).

## 9. Задание 4 — новая функциональность

Функции этого раздела добавлены после анализа исходной версии; они не заменяют описание исходной модели и требования разделов 1–8.

### Новые модели и связи

Добавлены модели `Watchlist` и `WatchlistItem` (пользовательский список, акция, ценовой порог и направление), `PriceAlertNotification` (событие уведомления), `Portfolio` и `PortfolioTrade` (портфель и журнал покупок/продаж), `PriceHistory` (исторические цены), `InvestmentStrategy` и `StrategyTrade` (параметры стратегии и журнал симуляции). Владелец списка, портфеля и стратегии — Django user; позиции связывают сущности с `Share`. Денежные поля хранятся как Decimal, ограничения базы данных запрещают неположительные цены/количества и дублирующие записи: [`dashboard/models.py`](./dashboard/models.py#L30-L228), [`dashboard/migrations/0008_investmentstrategy_portfolio_watchlist_watchlistitem_and_more.py`](./dashboard/migrations/0008_investmentstrategy_portfolio_watchlist_watchlistitem_and_more.py#L1-L178).

### Требования и подтверждения реализации

1. **Персональные списки.** Авторизованный пользователь создаёт свои списки наблюдения, добавляет/удаляет акции; доступ к чужим спискам запрещён. Подтверждение: [`dashboard/views.py`](./dashboard/views.py#L91-L142), [`dashboard/models.py`](./dashboard/models.py#L30-L81), [`dashboard/templates/dashboard/watchlists.html`](./dashboard/templates/dashboard/watchlists.html#L1-L40).
2. **Целевые цены и уведомления.** Для акции задаётся положительная цель и условие выше/ниже; уведомление создаётся один раз за непрерывный период выполнения условия и может сработать повторно после выхода цены из него. Подтверждение: [`dashboard/services/investments.py`](./dashboard/services/investments.py#L38-L64), [`dashboard/models.py`](./dashboard/models.py#L49-L92), [`dashboard/views.py`](./dashboard/views.py#L144-L152).
3. **Виртуальный портфель и история сделок.** Пользователь записывает покупки/продажи с количеством и ценой; продажа сверх текущей позиции отклоняется. Подтверждение: [`dashboard/services/investments.py`](./dashboard/services/investments.py#L101-L139), [`dashboard/views.py`](./dashboard/views.py#L154-L202), [`dashboard/models.py`](./dashboard/models.py#L95-L139).
4. **Расчёты портфеля.** Система отображает количество, среднюю себестоимость, оценку по последней цене, реализованный и нереализованный P/L. Подтверждение: [`dashboard/services/investments.py`](./dashboard/services/investments.py#L142-L203), [`dashboard/templates/dashboard/portfolio_detail.html`](./dashboard/templates/dashboard/portfolio_detail.html#L1-L46).
5. **Сохранение истории цен.** Успешная рыночная котировка сохраняется по акции и timestamp; повторный timestamp обновляет существующую точку. Подтверждение: [`dashboard/services/investments.py`](./dashboard/services/investments.py#L21-L35), [`dashboard/tasks.py`](./dashboard/tasks.py#L7-L24), [`dashboard/models.py`](./dashboard/models.py#L141-L158).
6. **Просмотр и анализ истории.** Пользователь выбирает период 7/30/90/180/365 дней и видит таблицу, график, абсолютное и процентное изменение цены. Подтверждение: [`dashboard/views.py`](./dashboard/views.py#L205-L234), [`dashboard/services/investments.py`](./dashboard/services/investments.py#L207-L230), [`dashboard/templates/dashboard/price_history.html`](./dashboard/templates/dashboard/price_history.html#L1-L35).
7. **Настройка и запуск стратегии.** Пользователь задаёт акцию, количество, условие покупки и/или продажи; активная стратегия при выполнении условий записывает симулированные сделки, не дублируя одну и ту же позицию на повторных проверках. Подтверждение: [`dashboard/models.py`](./dashboard/models.py#L161-L225), [`dashboard/services/investments.py`](./dashboard/services/investments.py#L67-L98), [`dashboard/tasks.py`](./dashboard/tasks.py#L19-L24).
8. **История и эффективность стратегии.** Владелец видит виртуальные сделки, позицию и P/L и может приостанавливать/возобновлять стратегию. Подтверждение: [`dashboard/services/investments.py`](./dashboard/services/investments.py#L233-L265), [`dashboard/views.py`](./dashboard/views.py#L235-L270), [`dashboard/templates/dashboard/strategies.html`](./dashboard/templates/dashboard/strategies.html#L1-L47).

Автоматическая часть функций 2, 5 и 7 зависит от доступного Tinkoff SDK, `TINKOFF_TOKEN`, Redis и запущенных Celery Beat/Worker; без внешнего источника приложение не генерирует поддельные рыночные цены: [`dashboard/services/market_data.py`](./dashboard/services/market_data.py#L1-L20), [`config/celery.py`](./config/celery.py#L13-L18).

## 10. Изменения и проверка

- Исправлены конфигурация запуска, URL пользовательского приложения, формы регистрации/входа и fallback-поведение рыночных сервисов: [`config/settings.py`](./config/settings.py#L1-L149), [`config/urls.py`](./config/urls.py#L4-L8), [`user/forms.py`](./user/forms.py#L1-L70), [`user/views.py`](./user/views.py#L1-L66), [`dashboard/services/graph.py`](./dashboard/services/graph.py#L1-L48), [`dashboard/services/market_data.py`](./dashboard/services/market_data.py#L1-L20).
- Для задания 4 добавлены модели, миграция, сервисы, страницы и тесты; инструкцию запуска обновлено в [`README.md`](./README.md#L1-L47).
- Проверки в текущем окружении: `manage.py check`, `makemigrations --check --dry-run`, полный `manage.py test` (23 теста) и HTTP-проверки основных маршрутов.
