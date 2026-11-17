# Новый сервер: контейнеры и данные в каталогах хоста

Сценарий для **нового Linux-сервера с пустыми каталогами**, обычным Docker
Engine и Docker Compose. PostgreSQL, ClickHouse, Metabase и API работают
в контейнерах. Постоянные данные размещаются в `/srv/profnavigator` на хосте.
Установка PostgreSQL или ClickHouse как системных служб не требуется.

Эта инструкция дополняет [развёртывание с нуля](deployment.md). Выберите
данный вариант **до первого запуска контейнеров**. На существующей установке
смена пути не переносит данные: для неё нужен отдельный согласованный перенос.
Приведённые ниже команды на рабочем окружении не выполнялись.

## 1. Где будут лежать данные

| Каталог Linux-хоста | Путь в контейнере | Содержимое |
|---|---|---|
| `/srv/profnavigator/postgres` | `db:/var/lib/postgresql/data` | Основная БД приложения и отдельная БД `metabase` |
| `/srv/profnavigator/clickhouse` | `clickhouse:/var/lib/clickhouse` | События, таблицы, представления и локальные метаданные аналитики |
| `/srv/profnavigator/uploads` | `api:/data/uploads` | Загруженные файлы и изображения |
| `/srv/profnavigator/infra` | `api:/app/storage/infra` | Реестры миграций ClickHouse, ID объектов Metabase, журналы и резервные копии инфраструктуры |

В Metabase дашборды, вопросы, подключения, пользователи и настройки находятся
в PostgreSQL, в БД `metabase`. Монтировать отдельную папку данных в контейнер
Metabase для этого не требуется. База приложения и БД Metabase используют
один контейнер `db`, но разные базы и учётные записи.

Код проекта и `.env` находятся в каталоге checkout. Сохраняйте их вместе
с перечнем версий образов; секреты и файлы данных не добавляйте в Git.

Redis в основном варианте остаётся временным хранилищем. Сохранение его
состояния отдельно описано в разделе 7.

## 2. Подготовить проект и окружение

Установите Docker Engine и Compose, получите проект с подмодулем `docs`.
Из [основной инструкции](deployment.md) выполните подготовку проекта и создание
нового `.env`, заполните пароли, адреса фронтендов и параметры HTTPS.
Все дальнейшие команды выполняйте из корня backend-проекта в Bash.

В `.env` оставьте адреса сервисов внутри сети Compose и задайте путь ClickHouse:

```dotenv
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=ryazan

COMPOSE_PROFILES=local-clickhouse
CLICKHOUSE_DATA_PATH=/srv/profnavigator/clickhouse
ANALYTICS_ENABLED=true
ANALYTICS_CLICKHOUSE_URL=http://clickhouse:8123

MB_DB_TYPE=postgres
MB_DB_HOST=db
MB_DB_PORT=5432
MB_DB_DBNAME=metabase
MB_DB_USER=metabase
```

Это только параметры размещения и подключения, а не полный `.env`. Обязательные
пароли `POSTGRES_PASSWORD`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_WRITER_PASSWORD`,
`CLICKHOUSE_READER_PASSWORD`, `MB_DB_PASS`, секреты и остальные поля заполняются
по основному руководству. Ссылку
`ANALYTICS_CLICKHOUSE_PASSWORD=${CLICKHOUSE_WRITER_PASSWORD}` сохраните.

`localhost` и `host.docker.internal` здесь не нужны: меняется место файлов,
а подключения по-прежнему идут между контейнерами.

## 3. Создать пустые каталоги и настроить права

Сначала убедитесь, что `/srv/profnavigator` расположен на нужном постоянном
диске и на нём достаточно места. Если используется отдельный диск, настройте
его монтирование при загрузке сервера до запуска Docker. Отсутствие диска
не должно приводить к запуску БД с другой пустой папкой.

Для текущих образов проекта пользователь PostgreSQL имеет UID/GID `70:70`,
ClickHouse — `101:101`. Значения проверены для используемых образов;
при их замене, rootless Docker или user namespace mapping проверьте владельцев
отдельно. Команды ниже рассчитаны на обычный Docker Engine на Linux.

Проверка запрещает продолжать поверх уже существующего каталога:

```bash
for task_directory in \
    /srv/profnavigator/postgres \
    /srv/profnavigator/clickhouse \
    /srv/profnavigator/uploads \
    /srv/profnavigator/infra
do
    if [ -e "$task_directory" ]; then
        printf 'Каталог уже существует: %s. Проверьте его содержимое до продолжения.\n' "$task_directory"
        exit 1
    fi
done

sudo install -d -m 0750 /srv/profnavigator
sudo install -d -m 0700 -o 70 -g 70 /srv/profnavigator/postgres
sudo install -d -m 0750 -o 101 -g 101 /srv/profnavigator/clickhouse
sudo install -d -m 0750 -o "$(id -u)" -g "$(id -g)" \
    /srv/profnavigator/uploads /srv/profnavigator/infra
```

Не исправляйте ошибки доступа через `chmod 777`. Проверьте владельца, права
и, если сервер использует SELinux, контекст монтируемых каталогов.

## 4. Добавить файл Compose для нового сервера

Создайте в корне проекта `docker-compose.host-storage.yml`:

```yaml
services:
  api:
    restart: unless-stopped
    command: ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
    volumes:
      - type: bind
        source: /srv/profnavigator/uploads
        target: /data/uploads
        bind:
          create_host_path: false
      - type: bind
        source: /srv/profnavigator/infra
        target: /app/storage/infra
        bind:
          create_host_path: false
  db:
    restart: unless-stopped
    volumes:
      - type: bind
        source: /srv/profnavigator/postgres
        target: /var/lib/postgresql/data
        bind:
          create_host_path: false
  clickhouse:
    volumes:
      - type: bind
        source: ${CLICKHOUSE_DATA_PATH:?Set CLICKHOUSE_DATA_PATH in .env}
        target: /var/lib/clickhouse
        bind:
          create_host_path: false
  redis:
    restart: unless-stopped
```

При объединении файлов Compose монтирования с одинаковым `target` заменяются.
Поэтому этот файл заменит `db_data` и локальные каталоги `storage/uploads`,
`storage/infra` на пути `/srv/...`; остальные настройки основного Compose,
включая образы, сеть и зависимости сервисов, сохранятся. `create_host_path: false`
не даёт Compose автоматически создать каталог при ошибке в его пути.

Основной Compose без этого дополнительного файла по-прежнему использует
том PostgreSQL `db_data`. Переменная `POSTGRES_DATA_PATH` основным файлом
не поддерживается: PostgreSQL переключается именно приведённым override.
Сама переменная `CLICKHOUSE_DATA_PATH` поддерживается основным Compose.

Используйте одну и ту же пару файлов во всех командах. Для текущего Bash-сеанса
определите сокращение:

```bash
dc() {
    docker compose -f docker-compose.yml -f docker-compose.host-storage.yml "$@"
}

dc config --quiet
```

Не запускайте полный `config` в общий журнал: он может вывести пароли.
Если используется дополнительный серверный файл из раздела HTTPS основного
руководства, добавляйте его третьим `-f` в функцию `dc` и сохраняйте это сочетание
во всех командах. Настройте публикацию портов и reverse proxy по тому разделу.

## 5. Первый запуск и инициализация

Выполняется **только на новой установке** с подготовленными пустыми каталогами:

```bash
dc build api
dc up -d --wait db redis clickhouse
dc ps

dc up -d --no-deps api
dc logs --tail 100 api
dc exec -T api alembic current
dc exec -T api alembic heads
```

API при старте автоматически применяет миграции PostgreSQL и заполняет
предусмотренные ими справочники. Дождитесь готовности API через
`http://127.0.0.1:<API_PORT>/openapi.json`. Ошибки приложения устраните до
дальнейшей инициализации; не очищайте хранилища для повторного запуска.

Подготовьте схему ClickHouse и служебную БД Metabase:

```bash
dc exec -T api python infra/clickhouse/scripts/update.py --check-env
dc exec -T api python infra/clickhouse/scripts/update.py --plan
dc exec -T api python infra/clickhouse/scripts/update.py --verify

dc exec -T api python infra/metabase/scripts/initialize_database.py
dc up -d --no-deps metabase
dc exec -T api python infra/metabase/scripts/deploy.py --check-env
dc exec -T api python infra/metabase/scripts/deploy.py --init
dc exec -T api python infra/metabase/scripts/deploy.py --all --plan
dc exec -T api python infra/metabase/scripts/deploy.py --all --verify
```

`update.py --verify` сначала применяет отсутствующие миграции ClickHouse,
затем проверяет объекты. Инициализация Metabase создаёт отдельную БД `metabase`
в том же PostgreSQL; физически её файлы попадут в `/srv/profnavigator/postgres`.

Создание администратора API, импорт банка викторины, подготовка контента,
согласий, устройств, настройка embedding и ключа Metabase описаны в разделах
7–8 [основного руководства](deployment.md). В командах этих разделов используйте
`dc` вместо `docker compose -f docker-compose.yml`. Один `deploy.py --init`
не настраивает всю систему и не устанавливает ключ embedding из `.env`.

## 6. Проверить фактические монтирования и готовность

Команды показывают только монтирования, без паролей из окружения контейнера:

```bash
docker inspect "$(dc ps -q db)" --format '{{json .Mounts}}'
docker inspect "$(dc ps -q clickhouse)" --format '{{json .Mounts}}'
docker inspect "$(dc ps -q api)" --format '{{json .Mounts}}'

dc exec -T db sh -c 'psql -X -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SHOW data_directory"'
dc exec -T db sh -c 'psql -X -U "$POSTGRES_USER" -d postgres -At' <<'SQL'
SELECT datname FROM pg_database
WHERE datname IN ('metabase', 'ryazan') ORDER BY datname;
SQL
```

У четырёх перечисленных выше каталогов должны быть `Type: bind`, нужный
`Source` и соответствующий `Destination`. Для PostgreSQL 16 `data_directory`
должен быть `/var/lib/postgresql/data`. Если `POSTGRES_DB` отличается от `ryazan`,
адаптируйте проверку имён БД.

Дождитесь успешных HTTP-проверок с учётом заданных в `.env` портов:

```bash
curl --fail --silent --show-error --retry 30 --retry-connrefused --retry-delay 2 \
    http://127.0.0.1:8000/openapi.json -o /dev/null
curl --fail --silent --show-error http://127.0.0.1:8124/ping
curl --fail --silent --show-error --retry 30 --retry-connrefused --retry-delay 2 \
    http://127.0.0.1:3001/api/health
```

Проверьте вход в CMS и Metabase, наличие коллекций и выполнение запросов
дашбордов. Файлы в `/srv/...` сохраняются при замене контейнеров; новый
контейнер должен подключаться к тем же путям и совместимой версии данных.

## 7. Если нужно сохранять также Redis

Redis содержит кеш и состояние текущих сценариев. В основном варианте выше
его сохранение не включено. Если его состояние тоже должно переживать
замену контейнера, выберите следующий вариант **до первого старта** нового Redis.
Подготовьте `/srv/profnavigator/redis` с правами пользователя Redis. У проверенного
образа `redis:7-alpine` UID/GID равны `999:1000`; при обновлении образа проверьте
значения отдельно. Для нового, ещё не существующего каталога:

```bash
if [ -e /srv/profnavigator/redis ]; then
    printf 'Каталог Redis уже существует; проверьте его до продолжения.\n'
    exit 1
fi
sudo install -d -m 0750 -o 999 -g 1000 /srv/profnavigator/redis
```

В том же `docker-compose.host-storage.yml` расширьте сервис `redis`:

```yaml
  redis:
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes", "--appendfsync", "everysec", "--dir", "/data"]
    volumes:
      - type: bind
        source: /srv/profnavigator/redis
        target: /data
        bind:
          create_host_path: false
```

Это включает AOF. При аварии возможна потеря последних примерно одной секунды
записей. Истечение TTL сохраняется; наличие файлов Redis не гарантирует
автоматическое продолжение игровых таймеров после простоя. Нужна отдельная
проверка прикладного восстановления. На существующем Redis смена команды
и монтирования требует отдельного плана переноса состояния.

## 8. Что резервировать

Сохраняйте PostgreSQL, включая **обе БД**, и ClickHouse средствами согласованного
резервирования; отдельно — `uploads`, `infra`, `.env` и серверные Compose-файлы.
При включённом сохранении Redis включите его данные в план резервирования.
Храните копии также вне этого сервера и проверяйте восстановление.

Обычное копирование файлов работающей БД может дать несогласованную копию.
Само расположение `/srv/...` не заменяет резервирование и не защищает
от удаления каталога или потери диска. Инструкции по резервированию приведены
в разделе [резервные копии и перенос](analytics/clickhouse-metabase.md#резервные-копии-и-перенос).

В исходной установке на Windows ничего менять для этого сценария не требуется.
Настройку, создание каталогов и первый запуск выполняйте на новом Linux-сервере.

Основания для правил монтирования: [объединение Compose-файлов](https://docs.docker.com/reference/compose-file/merge/),
[параметры bind mount](https://docs.docker.com/reference/compose-file/services/#volumes),
[хранилище образа PostgreSQL](https://hub.docker.com/_/postgres),
[сохранение Redis](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/).
