# Развёртывание проекта с нуля

Инструкция собирает в одном месте установку backend-проекта «ПрофНавигатор 62», PostgreSQL, Redis, ClickHouse, Metabase и документации. Команды основного сценария предназначены для **новой установки с пустыми хранилищами**. Все команды `docker compose` выполняются из корня backend-репозитория. Многострочные блоки с `<<'PY'` рассчитаны на Bash в Linux/WSL; однострочные Docker-команды подходят и для PowerShell.

Проверка выполнена 30.10.2026 на отдельном Compose-проекте с новыми контейнерами, сетью, томами и `.env`. Рабочее окружение не использовалось. Подробности проверки и ограничения приведены в конце страницы.

## 1. Что разворачивается

| Сервис | Назначение | Постоянные данные |
|---|---|---|
| `api` | FastAPI, REST `/api`, WebSocket, фоновые обработчики | `storage/uploads` → `/data/uploads`; `storage/infra` → `/app/storage/infra` |
| `db` | PostgreSQL 16: основная БД и отдельная служебная БД Metabase | Том `db_data` |
| `redis` | Redis 7: состояние игр и видеосценариев | В штатном Compose постоянного тома нет |
| `clickhouse` | События и представления аналитики | Том `clickhouse_data` |
| `metabase` | Вопросы, дашборды и встраиваемые графики | БД `metabase` в PostgreSQL |
| `adminer` | Необязательный интерфейс PostgreSQL | Собственного хранилища нет |

Фронтенды киосков, LED, планшета, CMS и личного кабинета, а также внешний сервис FaceAI в этот Compose не входят. Их сборка и содержимое медиатеки не появляются автоматически после запуска backend. Здесь подготавливаются серверное API и аналитика, к которым подключаются эти приложения.

Доступ к Git-серверу нужен для backend и подмодуля документации; доступ в интернет — для Docker Hub и Python-пакетов. Для полного стека заранее выделите ресурсы PostgreSQL, ClickHouse и JVM Metabase: последняя запускается с `-Xmx1g`; это не общий лимит памяти всего проекта. Контрольная сборка проверяла работоспособность, не производительность под нагрузкой.

## 2. Подготовка нового сервера

На уже подготовленном сервере достаточно Docker Engine в режиме Linux containers, Compose plugin, Git, Python 3 для подготовки `.env` и `curl` для проверок. Зависимости приложения устанавливаются **в образ API**.

Для чистого Ubuntu Server установка Docker из официального apt-репозитория:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git python3 nano
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker version
sudo docker compose version
```

Источник: [установка Docker Engine на Ubuntu](https://docs.docker.com/engine/install/ubuntu/). Это подготовка Linux-сервера; в контрольной сборке Docker Desktop уже был установлен. Дальнейшие команды предполагают доступ текущего пользователя к Docker; при необходимости добавляйте `sudo` перед `docker`. Конфликтующую существующую установку Docker не переустанавливайте по этой инструкции.

## 3. Получение исходников

```bash
git clone --recurse-submodules https://bucket.atlassys.tech/scm/rr/cms-backend.git ryazan
cd ryazan
git status --short
git submodule status
git -C docs status --short
git rev-parse HEAD
git -C docs rev-parse HEAD
```

Если backend уже клонирован, а `docs` отсутствует, из корня нового checkout выполните:

```bash
git submodule update --init --recursive
```

Подмодуль `docs` находится в отдельном репозитории `docs_esp.git`. Не добавляйте пароль или токен Git в URL. Для конкретного релиза используйте согласованный commit/tag backend и закреплённый им commit документации. Изменения в существующем checkout предварительно сохраните; команды получения подмодуля не предназначены для замены локальной работы.

## 4. Подготовка `.env` и каталогов

`.env.example` содержит незаполненные обязательные пароли. Запустить полный стек с одним копированием шаблона не получится. Следующий блок создаёт **новый** `.env`, не печатает секреты и отказывается перезаписывать существующий файл:

```bash
umask 077
python3 - <<'PY'
from pathlib import Path
import os
import secrets

path = Path('.env')
values = {
    'COMPOSE_PROJECT_NAME': 'ryazan',
    'POSTGRES_USER': 'ryazan',
    'METABASE_ADMIN_EMAIL': 'analytics-admin@example.org',
}
for key in (
    'POSTGRES_PASSWORD', 'JWT_SECRET_KEY', 'CLICKHOUSE_PASSWORD',
    'CLICKHOUSE_WRITER_PASSWORD', 'CLICKHOUSE_READER_PASSWORD',
    'MB_DB_PASS', 'METABASE_ADMIN_PASSWORD', 'METABASE_EMBEDDING_SECRET_KEY',
):
    values[key] = secrets.token_hex(32)
lines = []
for line in Path('.env.example').read_text(encoding='utf-8').splitlines():
    key = line.split('=', 1)[0]
    lines.append(key + '=' + values.pop(key) if key in values else line)
lines.extend(key + '=' + value for key, value in values.items())
descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(descriptor, 'w', encoding='utf-8') as output:
    output.write('\n'.join(lines) + '\n')
print('.env создан; секреты не выводятся')
PY

mkdir -p storage/uploads storage/infra
chmod 600 .env
```

Отредактируйте `.env` в редакторе до первого запуска:

```bash
nano .env
```

| Параметры | Что указать |
|---|---|
| `COMPOSE_PROJECT_NAME` | Постоянное имя новой установки. Для независимой проверки рядом с рабочим проектом — уникальное имя, например `ryazan-fresh-20261030`, выбранное **до** создания ресурсов |
| `POSTGRES_HOST`, `POSTGRES_PORT` | `db`, `5432` для штатного Compose |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `ryazan`, `ryazan` и сгенерированный пароль |
| `POSTGRES_DB_TEST` | `ryazan_test`; эта БД создаётся отдельно только для тестов |
| `REDIS_URL`, `REDIS_URL_TEST` | `redis://redis:6379/0` и `redis://redis:6379/1` |
| `API_PORT` | Свободный порт хоста; по умолчанию `8000`, для контрольной сборки `18000` |
| `JWT_SECRET_KEY` | Сгенерированный отдельный секрет |
| `AUTH_COOKIE_SECURE` | `false` только для локального HTTP; `true` для сервера с HTTPS |
| `AUTH_COOKIE_SAMESITE` | `lax` по умолчанию; `none` требует Secure и HTTPS |
| `AUTH_ALLOWED_ORIGINS` | JSON-массив точных адресов своих фронтендов со схемой и портом, без `*` и завершающего `/` |
| `DEVICE_AUTH_FRONTEND_URL` | Реальный адрес страницы `/device/auth` мобильного фронтенда; значение обязательно и должно быть HTTP(S) URL |
| `COMPOSE_PROFILES` | `local-clickhouse` для локального сервиса ClickHouse |
| `ANALYTICS_ENABLED`, `ANALYTICS_CLICKHOUSE_URL` | `true`, `http://clickhouse:8123` |
| `CLICKHOUSE_USER` | `analytics_admin` |
| `CLICKHOUSE_READER_USER`, `ANALYTICS_CLICKHOUSE_USER` | `analytics_reader`, `analytics_writer`: такие пользователи создаются штатной SQL-миграцией |
| `ANALYTICS_CLICKHOUSE_PASSWORD` | Оставить ссылку `${CLICKHOUSE_WRITER_PASSWORD}`, не задавать другой пароль |
| `CLICKHOUSE_PORT`, `METABASE_PORT` | `8124`, `3001`; при параллельной проверке `18124`, `13001` |
| `MB_DB_TYPE`, `MB_DB_HOST`, `MB_DB_PORT` | `postgres`, `db`, `5432` |
| `MB_DB_DBNAME`, `MB_DB_USER` | `metabase`, `metabase`: именно эту конфигурацию поддерживает `initialize_database.py` |
| `MB_DB_PASS` | Сгенерированный отдельный пароль |
| `METABASE_ADMIN_EMAIL`, `METABASE_ADMIN_PASSWORD` | Реальная почта и сгенерированный пароль веб-администратора Metabase |
| `MB_SITE_URL` | Адрес Metabase для браузера: локально `http://localhost:3001`, на сервере `https://analytics.example.org` |
| `METABASE_INTERNAL_URL` | `http://metabase:3000` внутри сети Compose |
| `METABASE_EMBEDDING_SECRET_KEY` | Сгенерированный отдельный ключ; его нужно установить и в Metabase на шаге 8 |

`MB_ANON_TRACKING_ENABLED=false` и `JAVA_TIMEZONE=Europe/Moscow` уже заданы в шаблоне. Пустые `DEMO_ADMIN_LOGIN/PASS`, OAuth и FaceAI допустимы, пока соответствующие интеграции не используются. `DEMO_ADMIN_*` не создают администратора и не заменяют CLI из шага 7.

Не выполняйте `source .env`: файл содержит значения в формате dotenv, включая JSON. Не выводите полный `docker compose config`: он раскрывает секреты. Безопасная проверка:

```bash
docker compose -f docker-compose.yml config --quiet
docker compose -f docker-compose.yml config --services
```

Далее везде явно указан `-f docker-compose.yml`: так случайный локальный `docker-compose.override.yml` не добавит публикацию Adminer на `8081`. PostgreSQL и Redis наружу не публикуются, ClickHouse и Metabase слушают `127.0.0.1`. API в основном Compose публикуется на всех интерфейсах: серверный вариант ниже ограничивает его localhost.

## 5. Сборка и запуск хранилищ

Для первой воспроизводимой проверки образ API собирается с обновлением базового образа и без кэша:

```bash
docker compose -f docker-compose.yml build --pull --no-cache api
docker compose -f docker-compose.yml up -d --wait db redis clickhouse
docker compose -f docker-compose.yml ps
```

Ожидаются `healthy` для трёх хранилищ. Создаются отдельные тома `<COMPOSE_PROJECT_NAME>_db_data` и `<COMPOSE_PROJECT_NAME>_clickhouse_data`. Не подключайте к контрольной сборке рабочие тома, `.env`, `storage/uploads` или журналы `storage/infra` другой установки.

Для проверки новой PostgreSQL до первого старта API:

```bash
docker compose -f docker-compose.yml exec -T db sh -c 'psql -X -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At' <<'SQL'
SELECT count(*) FROM pg_tables WHERE schemaname = 'public';
SQL
docker compose -f docker-compose.yml exec -T redis redis-cli DBSIZE
```

Обе команды должны вернуть `0`. Если это существующая установка, остановитесь и проверьте выбранный проект и хранилища; не очищайте их для продолжения инструкции.

## 6. API и миграции PostgreSQL

```bash
docker compose -f docker-compose.yml up -d --no-deps api
docker compose -f docker-compose.yml logs --tail 100 api
docker compose -f docker-compose.yml exec -T api alembic current
docker compose -f docker-compose.yml exec -T api alembic heads
curl --fail --silent --show-error --retry 30 --retry-connrefused --retry-delay 2 http://127.0.0.1:8000/openapi.json -o /dev/null
```

В URL замените `8000` на свой `API_PORT`. Успех: `Application startup complete`, HTTP 200, текущая Alembic-ревизия совпадает с `head`. В контрольной сборке — `0088`.

**Миграции выполняются автоматически** командой запуска `alembic upgrade head && uvicorn ...`; отдельный `upgrade` для новой установки не нужен. `up -d` означает запуск контейнера, а не готовность приложения: проверка HTTP обязательна. Для диагностики API используйте `/openapi.json`; специального `/health` в этой версии нет.

Seed-миграции загружают справочники и банк ПрофСтарт, а также копируют пять изображений ПрофСтарт в `storage/uploads/profstart`. Не запускайте произвольные reset/seed-скрипты поверх существующей базы.

## 7. Первый администратор и контент

Создайте администратора backend штатной интерактивной командой:

```bash
docker compose -f docker-compose.yml exec api python -m app.cli.create_admin \
  --email admin@example.org --first-name Admin --last-name Platform
```

Введите отдельный пароль на скрытом приглашении `Пароль:`. Не передавайте его в аргументах и не добавляйте в историю shell. При повторном запуске с тем же email команда откажется создавать дубликат. Это учётная запись CMS/API; веб-администратор Metabase создаётся отдельно.

Банк викторины находится в `app/data/quiz/professions_bank.json`. Его загрузка не входит в Alembic:

```bash
docker compose -f docker-compose.yml exec -T api python -m app.cli.load_quiz_bank --check
docker compose -f docker-compose.yml exec -T api python -m app.cli.load_quiz_bank
```

В контрольной сборке созданы 30 вопросов и два шаблона. Повтор использует совпадающие записи и не создаёт дубликаты; если контент уже изменён в CMS, импорт останавливается и не заменяет его.

### Видеозаглушка

Миграция `0018` создаёт запись `Placeholder video`, но **не создаёт сам** `/data/uploads/scenarios/placeholder.mp4`. В чистом checkout этот файл отсутствует. Для технической заглушки можно создать одну секунду чёрного видео, используя FFmpeg из зависимости `imageio-ffmpeg`; существующий файл команда не перезаписывает:

```bash
docker compose -f docker-compose.yml exec -T api python - <<'PY'
from pathlib import Path
import subprocess
import imageio_ffmpeg

target = Path('/data/uploads/scenarios/placeholder.mp4')
if target.exists():
    raise SystemExit('Файл уже существует; оставлен без изменений')
target.parent.mkdir(parents=True, exist_ok=True)
subprocess.run([
    imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error', '-n',
    '-f', 'lavfi', '-i', 'color=c=black:s=1280x720:r=25:d=1',
    '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(target),
], check=True)
print('Видеозаглушка создана')
PY
```

`DEFAULT_SCENARIO_VIDEO_ID` должен ссылаться на существующую запись этого файла; на чистой проверенной базе это ID `1`. Проверить фактическое значение без изменения БД:

```bash
docker compose -f docker-compose.yml exec -T db sh -c 'psql -X -U "$POSTGRES_USER" -d "$POSTGRES_DB"' <<'SQL'
SELECT id, title, file_path FROM files WHERE title = 'Placeholder video';
SQL
```

Для эксплуатации загрузите согласованные реальные материалы через CMS/API. Миграции создают типы согласий, но актуальный текст согласия `personal_data` нужно подготовить и опубликовать через CMS; без действующей версии гостевая регистрация не готова к использованию. Настройте устройства и их токены, опубликуйте нужные тесты и сценарии. Запуск контейнеров сам по себе эти действия не выполняет.

## 8. ClickHouse и Metabase

Сначала проверяется окружение, применяются миграции аналитики и создаётся служебная база Metabase. Metabase запускается **после** её подготовки:

```bash
docker compose -f docker-compose.yml exec -T api python infra/clickhouse/scripts/update.py --check-env
docker compose -f docker-compose.yml exec -T api python infra/clickhouse/scripts/update.py --plan
docker compose -f docker-compose.yml exec -T api python infra/clickhouse/scripts/update.py --verify

docker compose -f docker-compose.yml exec -T api python infra/metabase/scripts/initialize_database.py
docker compose -f docker-compose.yml up -d --no-deps metabase
docker compose -f docker-compose.yml exec -T api python infra/metabase/scripts/deploy.py --check-env
docker compose -f docker-compose.yml exec -T api python infra/metabase/scripts/deploy.py --init
docker compose -f docker-compose.yml exec -T api python infra/metabase/scripts/deploy.py --all --plan
docker compose -f docker-compose.yml exec -T api python infra/metabase/scripts/deploy.py --all --verify

curl -fsS http://127.0.0.1:8124/ping
curl -fsS http://127.0.0.1:3001/api/health
```

Замените порты на свои. Первый старт JVM и создание схемы Metabase могут занять несколько минут; `--init` ожидает готовность ограниченное время. Если время истекло, проверьте `logs --tail 100 metabase` и `/api/health`, затем повторите `--init`, не пересоздавая базы.

Ожидаемые результаты для проверенной версии: ClickHouse version `12`, проверка таблицы и представлений; Metabase — **84 managed card queries verified**. `--init` создаёт/проверяет подключение и реестр, но не загружает дашборды. Именно `--all --verify` разворачивает весь набор и выполняет запросы. `--plan` Metabase требует уже инициализированного сервиса. `--verify` ClickHouse также применяет ожидающие миграции; это не режим только чтения.

### Ключ встраивания графиков

На **новой** установке установите сгенерированный `METABASE_EMBEDDING_SECRET_KEY` в Metabase без вывода его значения. Скрипт использует штатный клиент проекта и переменные окружения контейнера:

```bash
docker compose -f docker-compose.yml exec -T api python - <<'PY'
import os
import sys
sys.path[:0] = ['/app/infra', '/app/infra/metabase/scripts']
from config import read_environment
from client import Metabase

api = Metabase(read_environment())
api.login(allow_setup=False)
api.request('PUT', 'setting/embedding-secret-key', {
    'value': os.environ['METABASE_EMBEDDING_SECRET_KEY'],
})
print('Ключ встраивания новой установки согласован')
PY
```

Штатный `deploy.py` включает Static embedding, но ключ из `.env` туда не устанавливает. При несовпадении ключей API выдаёт токен, который Metabase отклоняет. На существующем сервере сохраняйте текущий ключ из **Admin → Embedding → Static** и согласуйте с ним `.env`; не заменяйте его этой командой как обычную проверку: прежние embed-токены перестанут работать.

Реестры `storage/infra/clickhouse/versions.json` и `storage/infra/metabase/state.json` создаются автоматически. Не копируйте их с другого независимого окружения: версии и ID должны относиться к его собственным БД. Подробности — [ClickHouse и Metabase](analytics/clickhouse-metabase.md).

## 9. Проверка установки

```bash
docker compose -f docker-compose.yml ps
docker compose -f docker-compose.yml exec -T db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose -f docker-compose.yml exec -T redis redis-cli ping
docker compose -f docker-compose.yml exec -T api alembic current
docker compose -f docker-compose.yml exec -T api python infra/clickhouse/scripts/update.py --plan
docker compose -f docker-compose.yml exec -T api python infra/metabase/scripts/deploy.py --verify
curl -fsS http://127.0.0.1:8000/openapi.json -o /dev/null
curl -fsS http://127.0.0.1:8124/ping
curl -fsS http://127.0.0.1:3001/api/health
```

Ожидаются готовые сервисы, `PONG`, актуальный Alembic head, пустой список ожидающих миграций ClickHouse и успешные запросы Metabase. Проверить функционально:

1. Войти администратором через CMS либо `http://localhost:8000/demo/metabase`.
2. Проверить справочники профессий и тестов ПрофСтарт.
3. Проверить отображение картинок ПрофСтарт и загруженных видео.
4. Открыть Metabase, войти с `METABASE_ADMIN_EMAIL/PASSWORD`, открыть коллекцию «Аналитика».
5. На `/demo/metabase` проверить запрос данных встроенного графика. Это дополнительно проверяет реестр и совпадение ключей подписи.
6. Проверить гостевую регистрацию после публикации согласия и подключения фронтенда.

Для входа в локально опубликованный Metabase с другого компьютера:

```bash
ssh -N -L 3001:127.0.0.1:3001 user@server.example.org
```

Откройте `http://localhost:3001`; правый порт туннеля должен совпадать с `METABASE_PORT` сервера. Adminer необязателен: запустить его без публикации наружу можно командой `docker compose -f docker-compose.yml up -d --no-deps adminer`.

### Тесты на отдельной БД

Этот раздел нужен для контрольного стенда. Фикстуры pytest очищают тестовую PostgreSQL через `TRUNCATE` и Redis через `FLUSHDB`; не указывайте рабочую базу или Redis DB. Ниже `createdb` выполняется один раз в новой установке с ещё отсутствующей `ryazan_test`. Сервис `db` не получает `POSTGRES_DB_TEST` в своём environment из штатного Compose, поэтому имя нужно указать явно, в соответствии с `.env`:

```bash
docker compose -f docker-compose.yml exec -T db sh -c 'createdb -U "$POSTGRES_USER" ryazan_test'
```

Проверьте изоляцию внутри API перед запуском:

```bash
docker compose -f docker-compose.yml exec -T api python - <<'PY'
import os
from urllib.parse import urlsplit
from app.core.config import settings

assert settings.postgres_host == 'db'
assert os.environ['POSTGRES_DB_TEST'] == 'ryazan_test'
assert settings.postgres_db != os.environ['POSTGRES_DB_TEST']
app, test = urlsplit(settings.redis_url), urlsplit(os.environ['REDIS_URL_TEST'])
assert app.hostname == test.hostname == 'redis'
assert (app.port or 6379) == (test.port or 6379) == 6379
assert app.path == '/0' and test.path == '/1'
print('Отдельная PostgreSQL ryazan_test; Redis приложения /0, тестов /1')
PY

docker compose -f docker-compose.yml exec -T \
  -e 'AUTH_ALLOWED_ORIGINS=["http://localhost:5173"]' -e AUTH_COOKIE_SECURE=true \
  api pytest tests/ -q -x
docker compose -f docker-compose.yml exec -T api python -m unittest discover -s infra/tests -q
```

Авторизационные фикстуры используют Origin `http://localhost:5173` и HTTPS. Эти overrides действуют только в процессе pytest и не добавляют тестовый origin в настройки работающего API. Без них на сервере с другим списком origins возможны 403 при корректном приложении. Alembic применяет тестовую схему автоматически; `createdb` нужна, потому что PostgreSQL-образ создаёт только основную БД.

## 10. Сборка документации

Документация — отдельный checkout `docs`. Для изолированной сборки на Linux можно использовать отдельный контейнер Python; уникальное имя задаётся для каждой новой контрольной сборки:

```bash
docker run --name ryazan-docs-build-20261030 \
  --mount "type=bind,src=$(pwd)/docs,dst=/docs" -w /docs \
  python:3.12-slim sh -c 'pip install --no-cache-dir mkdocs mkdocs-material && python -m mkdocs build -d public && cp docs/api/scalar.html public/api/scalar.html'
```

Результат — `docs/public/`; опубликуйте содержимое каталога на статическом веб-сервере. MkDocs hook собирает итоговую OpenAPI-спецификацию, затем копируется Scalar. Это те же шаги, что в `build.sh`, но без зависимости от LF/CRLF shell-скрипта: при сборке Windows-checkout в Linux-контейнере прямой `bash build.sh` создал некорректный путь из-за CRLF. Node.js и Prism нужны только для отдельного mock-сервера разработки, не для backend или этой сборки документации. Контейнер сборки после завершения остаётся остановленным.

## 11. Публикация на сервере и постоянная эксплуатация

Для доступа пользователей нужны DNS, HTTPS и reverse proxy к API и Metabase. Для API нужно передавать WebSocket Upgrade; для Metabase — корректные `Host` и `X-Forwarded-Proto`. В `.env` задайте реальные `AUTH_ALLOWED_ORIGINS`, `DEVICE_AUTH_FRONTEND_URL`, `MB_SITE_URL` и `AUTH_COOKIE_SECURE=true` **до** запуска. Настройка сертификатов и отдельных фронтендов зависит от инфраструктуры сервера и в контрольной сборке не проверялась.

Штатный Compose запускает Uvicorn с `--reload`, публикует API на всех интерфейсах и не задаёт автоперезапуск всем сервисам. Для новой серверной установки можно заранее создать `docker-compose.server.yml`:

```yaml
services:
  api:
    restart: unless-stopped
    ports: !override
      - "127.0.0.1:${API_PORT:-8000}:8000"
    command: ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
  db:
    restart: unless-stopped
  redis:
    restart: unless-stopped
```

Этот вариант требует Compose с поддержкой `!override` (2.24.4+). **Выберите его до создания серверных контейнеров** и во всех командах выше добавляйте второй файл: `docker compose -f docker-compose.yml -f docker-compose.server.yml ...`. Не применяйте его к работающим PostgreSQL/Redis ради проверки документации. Здесь Redis по-прежнему без постоянного тома: после рестарта состояние незавершённых сценариев может потеряться; стратегию его сохранения нужно выбирать отдельно.

В текущей версии подключён временный `GET /api/auth/{id}`, выдающий тестовый пользовательский токен; в исходнике есть TODO удалить его перед production. Перед публичным открытием API этот маршрут нужно отключить отдельной правкой. Его наличие не мешает изолированной контрольной сборке, но запуск стека не означает готовность текущей версии к публичной эксплуатации.

Для OAuth заполните выданные провайдерами параметры `OAUTH_*`. Для FaceAI задайте `FACEAI_BASE_URL`, `FACEAI_API_KEY` и независимый `FACEAI_WEBHOOK_TOKEN`; во внешнем FaceAI согласуйте `KERNEL_WEBHOOK_URL=https://<api-domain>/api/faceai/webhook` и тот же входящий токен. Без адреса и ключа FaceAI отправка заданий отключена. Эти внешние сервисы данной инструкцией не устанавливаются.

### Обновление и сохранение данных

Сохраняйте вместе: PostgreSQL (основную БД и `metabase`), данные ClickHouse, `.env`, `storage/uploads` и `storage/infra`. Файлы коллекций в Git не заменяют резервную копию БД Metabase. Резервирование и перенос описаны на странице [ClickHouse и Metabase](analytics/clickhouse-metabase.md).

`requirements.txt` в основном не фиксирует версии Python-пакетов, `python:3.12-slim`, PostgreSQL и Redis также используют изменяемые теги. Поэтому будущая сборка без кэша может получить другой набор зависимостей. Для поставки зафиксируйте проверенный образ и сохраните список его пакетов:

```bash
docker compose -f docker-compose.yml exec -T api pip freeze > api-requirements-built.txt
docker compose -f docker-compose.yml images
```

Для обновления существующего сервера сначала проверьте миграции и сделайте необходимые резервные копии. Сборка не применяет миграции; запуск нового API применяет их автоматически:

```bash
docker compose -f docker-compose.yml build api
docker compose -f docker-compose.yml up -d --no-deps api
docker compose -f docker-compose.yml exec -T api alembic current
```

На серверном варианте используйте оба Compose-файла. Изменение `.env` требует обновления окружения контейнера через `up`, одного `restart` недостаточно. Не меняйте существующий пароль PostgreSQL только в `.env`: инициализация образа не меняет пароль роли в уже заполненном томе. `down`, `down -v`, `rm`, `prune`, очистка БД и изменение имени проекта не являются шагами развёртывания или устранения ошибок этой инструкции.

## 12. Частые проблемы

| Симптом | Проверка и действие |
|---|---|
| Compose требует `CLICKHOUSE_PASSWORD` или `MB_DB_PASS` | Заполнить `.env`; обязательные подстановки проверяются при разборе Compose, даже при запуске отдельного сервиса |
| PostgreSQL/Redis не `healthy` | `docker compose -f docker-compose.yml logs --tail 100 db redis`; проверить ресурсы и хранилища |
| API не отвечает после `up -d` | `logs --tail 100 api`; дождаться окончания миграций; проверить валидность настроек и `API_PORT` |
| Metabase пишет, что БД не существует | При работающем API выполнить `initialize_database.py`, затем запуск Metabase и `deploy.py --init` |
| Metabase открылся, но нет отчётов | Выполнить `deploy.py --all --verify`; одного `--init` недостаточно |
| В iframe ошибка подписи | Сверить существующий Static embedding secret с `METABASE_EMBEDDING_SECRET_KEY`; проверить, что API получил актуальное окружение |
| Регистрация или login возвращают 403 | Проверить точный Origin/Referer и `AUTH_ALLOWED_ORIGINS`, HTTPS и cookie-настройки |
| Гостевая регистрация недоступна | Проверить опубликованное действующее согласие `personal_data` |
| Видео/изображение возвращает 404 | Проверить `storage/uploads` и фактический файл, а не только запись в `files`; для чистой установки подготовить видеозаглушку |
| `Applied migration changed` ClickHouse | Использован журнал другой установки либо изменён уже применённый SQL; не исправлять checksums вручную и не удалять журнал |
| Порт занят | Для новой независимой установки заранее выбрать свои порты в `.env`; существующие сервисы не останавливать |

Полные логи и содержимое `.env` могут содержать чувствительные данные; перед передачей диагностических файлов их нужно проверить.

## 13. Результат контрольной сборки 30.10.2026

Проверялся backend `2866ec0` и документация `a865595`: отслеживаемые исходники скопированы в отдельный каталог, без рабочей `.env`, БД, загруженных файлов и реестров аналитики. Имя проекта `ryazan-fresh-20261030`; API `18000`, ClickHouse `18124`, Metabase `13001`. Использовались Docker Desktop с Linux Engine 29.6.1 и Compose 5.2.0. Установка пакетов Ubuntu, удалённый `git clone`, DNS, TLS, прокси и внешние интеграции в этот прогон не входили.

| Проверка | Результат |
|---|---|
| `build --pull --no-cache api` | Образ собран из исходников; зависимости установлены заново |
| Новые PostgreSQL и Redis до старта API | 0 таблиц и 0 ключей |
| Миграции PostgreSQL | Полная цепочка с нуля до `0088 (head)` |
| ClickHouse | 12 миграций; таблица и все проверяемые представления доступны |
| Metabase | Новая служебная БД и администратор, все коллекции; 84 SQL-запроса проверены |
| Первый администратор backend | Создан через `app.cli.create_admin`; HTTP login успешен |
| HTTP API | `/openapi.json` — 200, 166 путей; справочники, ПрофСтарт, кабинет сотрудника и каталог аналитики — 200 |
| Встраивание Metabase | Выдан токен API и выполнен embedded query — HTTP 200 |
| PDF-отчёт аналитики | HTTP 200, корректная PDF-сигнатура |
| Банк викторины | 30 вопросов и 2 шаблона; повтор не создаёт дубликаты |
| Медиа | 5 картинок ПрофСтарт созданы миграцией и доступны; недостающая видеозаглушка создана отдельной командой |
| Инфраструктурные тесты | 83 теста, OK |
| Документация | MkDocs и Scalar собраны; новая страница и навигация проверены. Три существующих предупреждения о ссылках в `changelog/docs/v1.15.md`, новых предупреждений от страницы нет |
| Полный pytest | 1796 passed, 40 subtests passed, 3 предупреждения SQLAlchemy в существующих изолированных тестах; 710,55 с |

Набор команд выявил три обязательных дополнительных шага для чистой установки: загрузка банка викторины, создание файла видеозаглушки и согласование секрета встраивания. Изменений кода приложения для успешной сборки и инициализации не потребовалось.
