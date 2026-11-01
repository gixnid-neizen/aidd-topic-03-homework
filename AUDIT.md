# Технический аудит проекта

## Область и методика

Отчёт фиксирует состояние исходной реализации и оставшиеся проблемы на этапе задания 3, после модернизации, но до изменений задания 4 (1 ноября 2026 г.). Указанные номера строк относятся к коду этапа 3; в последующих коммитах отдельные строки могли сдвинуться. Задание 3 уже устранило часть первоначальных дефектов — в частности, повреждённые вызовы в сценариях входа/регистрации и исходную конфигурацию БД. Ниже это не представлено как неисправленное состояние.

Версии-кандидаты в таблице зависимостей — последние опубликованные на PyPI на дату аудита; проверены версия и `Requires-Python`. Это не результат интеграционного тестирования обновлённого набора. Совместимость всего приложения, особенно при переходе между основными версиями Django, требует отдельного прогона тестов.

## 1. Устаревшие библиотеки и зависимости

В `requirements.txt` закреплены следующие версии. Текущие версии и ограничения Python сверены с метаданными [PyPI JSON API](https://pypi.org/pypi/); для Django диапазон Python дополнительно сверялся с [официальной таблицей совместимости Django](https://docs.djangoproject.com/en/6.1/faq/install/).

| Пакет | Закреплено в проекте | Последняя опубликованная версия на 2026-11-01 | Requires-Python последней версии |
|---|---:|---:|---|
| [amqp](https://pypi.org/project/amqp/) | 5.2.0 | 5.4.1 | >=3.10 |
| [asgiref](https://pypi.org/project/asgiref/) | 3.8.1 | 3.13.0 | >=3.11 |
| [billiard](https://pypi.org/project/billiard/) | 4.2.1 | 4.3.1 | >=3.10 |
| [celery](https://pypi.org/project/celery/) | 5.5.3 | 5.6.3 | >=3.9 |
| [crispy-bootstrap3](https://pypi.org/project/crispy-bootstrap3/) | 2024.1 | 2024.1 | >=3.7 |
| [Django](https://pypi.org/project/Django/) | 4.2.23 | 6.1.2 | >=3.12; Django 6.1 поддерживает Python 3.12–3.14 |
| [django-crispy-forms](https://pypi.org/project/django-crispy-forms/) | 2.3 | 2.7 | >=3.10 |
| [django-filter](https://pypi.org/project/django-filter/) | 24.3 | 26.2 | >=3.11 |
| [djangorestframework](https://pypi.org/project/djangorestframework/) | 3.15.2 | 3.18.3 | >=3.10 |
| [grpcio](https://pypi.org/project/grpcio/) | 1.71.0 | 1.85.1 | >=3.10 |
| [kombu](https://pypi.org/project/kombu/) | 5.5.4 | 5.6.2 | >=3.9 |
| [plotly](https://pypi.org/project/plotly/) | 6.0.1 | 7.1.0 | >=3.8 |
| [pydantic](https://pypi.org/project/pydantic/) | 2.10.6 | 2.14.2 | >=3.10 |
| [python-dateutil](https://pypi.org/project/python-dateutil/) | 2.9.0.post0 | 4.0.0 | >=3.11 |
| [redis](https://pypi.org/project/redis/) | 5.2.1 | 8.1.0 | >=3.10 |

Источник закреплённых версий: [`requirements.txt`](./requirements.txt#L1-L15). Кроме `crispy-bootstrap3`, закреплённые версии отстают от последних опубликованных; `Django==4.2.23` относится к ветке 4.2, для которой официально поддерживаются Python 3.8–3.12, а поддержка безопасности закончилась в апреле 2026 года. На дату аудита актуальная опубликованная ветка Django 6.1 поддерживает Python 3.14. Одного совпадения `Requires-Python` недостаточно, чтобы подтвердить совместимость всех обновлений с приложением.

В манифесте нет драйвера PostgreSQL и SDK Tinkoff, хотя проект содержит настройки для PostgreSQL и код рыночных данных. SDK импортируется как необязательная зависимость, поэтому при его отсутствии данные рынка не загружаются; без драйвера выбор PostgreSQL не запускается. Это следует учитывать при оценке полноты окружения: [`requirements.txt`](./requirements.txt#L1-L15), [`config/settings.py`](./config/settings.py#L92-L109), [`dashboard/services/market_data.py`](./dashboard/services/market_data.py#L1-L20).

## 2. Совместимость и конфигурация

- **Python 3.14 и Django.** Закреплённый Django 4.2.23 официально поддерживает Python только до 3.12. Для Python 3.14 следует использовать версию Django с подтверждённой поддержкой этой версии Python; на дату аудита это Django 5.2.8+, 6.0 или 6.1. В проекте минимальная/максимальная версия Python отдельно не объявлена: [`requirements.txt`](./requirements.txt#L1-L15). Проверка поддержки: [Django: What Python version can I use?](https://docs.djangoproject.com/en/6.1/faq/install/).
- **SECRET_KEY.** Переменная окружения используется, но при её отсутствии подставляется предсказуемое значение `dev-secret-key-for-local-project`; это небезопасно для развёртывания: [`config/settings.py`](./config/settings.py#L7-L7).
- **DEBUG и ALLOWED_HOSTS.** `DEBUG=True` и `ALLOWED_HOSTS=["*"]` оставлены без разделения dev/prod-конфигураций: [`config/settings.py`](./config/settings.py#L9-L11).
- **База данных.** SQLite используется по умолчанию. В режиме PostgreSQL имя, пользователь и пароль имеют локальные значения по умолчанию, а порт БД опубликован контейнером; в `requirements.txt` отсутствует PostgreSQL-драйвер. Секреты compose-файла совпадают с локальными default-настройками: [`config/settings.py`](./config/settings.py#L92-L109), [`docker-compose.yml`](./docker-compose.yml#L3-L14), [`requirements.txt`](./requirements.txt#L1-L15).
- **Внешние сервисы.** При пустом `TINKOFF_TOKEN` или отсутствии SDK приложение продолжает запуск, но сервис возвращает пустые данные; это ограничивает актуальность цен и графиков: [`config/settings.py`](./config/settings.py#L139-L146), [`dashboard/services/market_data.py`](./dashboard/services/market_data.py#L9-L20).

## 3. Ошибки проектирования и реализации

- Карточка инструмента обращается к записи через `Share.objects.get(id=pk)` без преобразования `DoesNotExist` в HTTP 404. Несуществующий ID приводит к необработанной ошибке сервера: [`dashboard/views.py`](./dashboard/views.py#L29-L39).
- API использует `ModelViewSet` со стандартными действиями записи и не задаёт `permission_classes`; в конфигурации DRF также нет ограничения прав. В результате API не требует аутентификации для создания, изменения и удаления записей: [`dashboard/api/v1/views.py`](./dashboard/api/v1/views.py#L16-L22), [`config/settings.py`](./config/settings.py#L32-L36), [`dashboard/api/v1/router.py`](./dashboard/api/v1/router.py#L5-L6).
- HTML CRUD ограничен только фактом входа. Любой вошедший пользователь может создавать, редактировать и удалять записи общего каталога; разграничения ролей/владения нет: [`dashboard/views.py`](./dashboard/views.py#L11-L17), [`dashboard/views.py`](./dashboard/views.py#L41-L63).
- Форма регистрации сравнивает пароли, но не вызывает `validate_password()`; заданные в settings валидаторы паролей поэтому не применяются этой формой. Проверка уникальности email выполняется до записи и не обеспечена уникальным ограничением поля email у стандартной модели пользователя: [`config/settings.py`](./config/settings.py#L111-L124), [`user/forms.py`](./user/forms.py#L29-L53), [`user/models.py`](./user/models.py#L1-L3).
- Задача обновления цены игнорирует полученное время котировки. При `get_last_data() == (None, None)` сравнение с `None` вызывает исключение, после чего задача записывает `last_price=None` и восходящий тренд. Ошибка внутри цикла только журналируется; вызывающая сторона не получает признак частичного сбоя: [`dashboard/tasks.py`](./dashboard/tasks.py#L7-L28), [`dashboard/services/market_data.py`](./dashboard/services/market_data.py#L9-L20).
- При записи через `QuerySet.update()` автоматически не обновляется `auto_now`-поле `updated_at`; сохранённое время обновления может не соответствовать последнему обновлению цены: [`dashboard/tasks.py`](./dashboard/tasks.py#L24-L26), [`dashboard/models.py`](./dashboard/models.py#L13-L17).
- В задаче Celery расписание равно 10 секундам, хотя имя задачи говорит «every-5-min»; вычисленное расписание и его имя противоречат друг другу. В settings также оставлена закомментированная альтернативная конфигурация broker: [`config/celery.py`](./config/celery.py#L13-L17), [`config/settings.py`](./config/settings.py#L141-L146).
- `get_graph()` подавляет любые исключения без логирования и возвращает одну общую заглушку, из-за чего ошибка внешнего API или данных не диагностируется: [`dashboard/services/graph.py`](./dashboard/services/graph.py#L15-L48).

## 4. Миграции и модель данных

- Миграция добавляет `uid` как уникальное поле с общим временным default `""` и не сохраняет default. На уже заполненной таблице одинаковое значение для существующих строк конфликтует с `unique=True`; путь миграции существующей БД требует отдельной проверки/плана заполнения: [`dashboard/migrations/0003_add_uuid.py`](./dashboard/migrations/0003_add_uuid.py#L11-L17).
- В миграции `0004` поле `name` временно получает неверный `verbose_name="Валюта"`, а `ticker` — усечённый `"Ти"`; следующие миграции меняют подписи. Текущая модель исправлена, но цепочка отражает несогласованное промежуточное состояние: [`dashboard/migrations/0004_add_last_price.py`](./dashboard/migrations/0004_add_last_price.py#L24-L38), [`dashboard/migrations/0005_add_verbose_name.py`](./dashboard/migrations/0005_add_verbose_name.py#L11-L17), [`dashboard/migrations/0006_add_verbose_name.py`](./dashboard/migrations/0006_add_verbose_name.py#L11-L16).
- Рыночная цена хранится во `FloatField`, что не гарантирует точное десятичное представление финансовых значений. `isin` не уникален, хотя `figi`, `ticker` и `uid` имеют ограничения уникальности; модель не содержит явной проверки согласованности этих идентификаторов: [`dashboard/models.py`](./dashboard/models.py#L4-L17).
- История изменения цен исходной схемой не сохраняется: есть только одно поле последней цены и timestamp, а отдельной сущности точек котировки в моделях этого этапа нет: [`dashboard/models.py`](./dashboard/models.py#L4-L17).

## 5. Представления, шаблоны и безопасность

- `ShareModelForm` использует `fields="__all__"`, поэтому CRUD-форма выставляет пользователю все поля модели, включая внутренние идентификаторы; ограничение доступа только по `is_authenticated` не разделяет права пользователя: [`dashboard/forms.py`](./dashboard/forms.py#L6-L11), [`dashboard/templates/dashboard/create.html`](./dashboard/templates/dashboard/create.html#L13-L19), [`dashboard/views.py`](./dashboard/views.py#L11-L17).
- В шаблоне карточки график выводится с отключённым автоэкранированием. Сейчас значение формирует серверный Plotly, но граница доверия зависит от того, какие данные попадают в HTML-графика: [`dashboard/templates/dashboard/detail.html`](./dashboard/templates/dashboard/detail.html#L19-L28), [`dashboard/services/graph.py`](./dashboard/services/graph.py#L31-L46).
- Выход из учётной записи выполняется GET-запросом и доступен обычной ссылкой; изменение состояния через GET допускает нежелательный межсайтовый выход пользователя: [`user/views.py`](./user/views.py#L60-L66), [`dashboard/templates/dashboard/base.html`](./dashboard/templates/dashboard/base.html#L36-L43).
- Frontend подтягивает библиотеки по внешним CDN; адрес Plotly использует `plotly-latest` без явного номера версии. Работа страницы зависит от CDN, а используемая версия не зафиксирована в проекте: [`dashboard/templates/dashboard/base.html`](./dashboard/templates/dashboard/base.html#L9-L24).
- Положительная мера: CSRF middleware включён, а формы входа, регистрации, создания и удаления содержат CSRF-токены: [`config/settings.py`](./config/settings.py#L62-L70), [`user/templates/user/auth.html`](./user/templates/user/auth.html#L3-L4), [`user/templates/user/registration.html`](./user/templates/user/registration.html#L4-L5), [`dashboard/templates/dashboard/create.html`](./dashboard/templates/dashboard/create.html#L13-L15), [`dashboard/templates/dashboard/delete.html`](./dashboard/templates/dashboard/delete.html#L9-L12).

## 6. Приоритеты

Приоритеты предполагают размещение приложения в сети или использование реальных учётных записей. Для локального учебного запуска часть конфигурационных рисков ниже, но перед production они блокирующие.

| Приоритет | Проблема | Файлы и строки |
|---|---|---|
| критично | Неаутентифицированный CRUD через API; пользователь извне может менять общий каталог | [`dashboard/api/v1/views.py`](./dashboard/api/v1/views.py#L16-L22), [`config/settings.py`](./config/settings.py#L32-L36), [`dashboard/api/v1/router.py`](./dashboard/api/v1/router.py#L5-L6) |
| критично | Непроизводственные настройки безопасности: известный fallback `SECRET_KEY`, `DEBUG=True`, разрешены любые hosts | [`config/settings.py`](./config/settings.py#L7-L11) |
| критично | Миграция уникального `uid` с одинаковым временным default может не примениться к существующей непустой БД | [`dashboard/migrations/0003_add_uuid.py`](./dashboard/migrations/0003_add_uuid.py#L11-L17) |
| важно | Django 4.2.23 не поддерживает Python 3.14; ветка 4.2 завершила период security support | [`requirements.txt`](./requirements.txt#L6-L6), [официальная таблица Django](https://docs.djangoproject.com/en/6.1/faq/install/) |
| важно | PostgreSQL-режим настроен без драйвера в зависимостях; используются известные значения доступа и опубликован порт БД | [`requirements.txt`](./requirements.txt#L1-L15), [`config/settings.py`](./config/settings.py#L99-L109), [`docker-compose.yml`](./docker-compose.yml#L3-L14) |
| важно | Задача может очищать цену при отсутствующей котировке; timestamp цены не используется, а `updated_at` не обновляется queryset-операцией | [`dashboard/tasks.py`](./dashboard/tasks.py#L11-L28), [`dashboard/models.py`](./dashboard/models.py#L13-L17) |
| важно | Пользовательская форма регистрации не применяет настроенные валидаторы паролей; email не закреплён уникальным ограничением пользовательской модели | [`config/settings.py`](./config/settings.py#L111-L124), [`user/forms.py`](./user/forms.py#L29-L53), [`user/models.py`](./user/models.py#L1-L3) |
| важно | Любой вошедший пользователь может редактировать и удалять общие записи; форма объявляет все поля модели доступными | [`dashboard/views.py`](./dashboard/views.py#L11-L17), [`dashboard/views.py`](./dashboard/views.py#L41-L63), [`dashboard/forms.py`](./dashboard/forms.py#L6-L11) |
| важно | Некорректный ID карточки приводит к 500 вместо 404 | [`dashboard/views.py`](./dashboard/views.py#L29-L39) |
| желательно | `FloatField` для денежных значений допускает погрешности двоичного представления; `isin` не уникален | [`dashboard/models.py`](./dashboard/models.py#L7-L17) |
| желательно | График подавляет исключения; имя и интервал расписания Celery расходятся; есть закомментированная конфигурация broker | [`dashboard/services/graph.py`](./dashboard/services/graph.py#L15-L48), [`config/celery.py`](./config/celery.py#L13-L17), [`config/settings.py`](./config/settings.py#L141-L146) |
| желательно | Выход меняет состояние через GET; frontend использует внешние JS CDN и незакреплённый `plotly-latest` | [`user/views.py`](./user/views.py#L60-L66), [`dashboard/templates/dashboard/base.html`](./dashboard/templates/dashboard/base.html#L9-L24) |
