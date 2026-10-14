# Аналитика

## AnalyticsEvent

Бэкенд создаёт события, отправитель сохраняет их в общей таблице ClickHouse
`analytics.events`. Сейчас подключены индивидуальная и командная викторины.
Сервисы вызывают `app.services.analytics.emit_event`; HTTP API приёма событий
от внешних устройств пока не реализован.

### Атрибуты

| Поле | Тип ClickHouse | Описание |
|---|---|---|
| `id` | UUID | Уникальный ID конкретного факта; сохраняется при повторах |
| `event_id` | UInt16 | Действие из `EventType(IntEnum)` |
| `module_id` | UInt8 | Функциональный модуль из `ModuleType(IntEnum)` |
| `software_id` | UInt8 | Программный комплекс из `SoftwareType(IntEnum)` |
| `device_type` | Nullable(UInt8) | Оборудование из `DeviceType(IntEnum)`; NULL, если не передано |
| `device_id` | Nullable(Int64) | Конкретное устройство |
| `user_id` | Nullable(Int64) | Пользователь действия, если известен |
| `session_id` | Nullable(Int64) | ID сессии соответствующего модуля |
| `occurred_at` | DateTime64(3, UTC) | Время действия |
| `received_at` | DateTime64(3, UTC) | Назначается ClickHouse при вставке |
| `payload` | String | JSON с параметрами конкретного события |

В Python payload передаётся словарём. Enum проверяются и сериализуются в числа
до помещения в очередь. ORM-объекты и AsyncSession в очередь не передаются.
Коды и названия перечислены в [типах событий](../references/analytics-event-types.md)
и [источниках событий](../references/event-sources.md). После публикации коды
не перенумеровываются и не назначаются другому значению.

`device_type` и `device_id` по умолчанию равны NULL. Значения передаются только
при наличии соответствующих данных. В коде оставлен TODO для определения типа
оборудования по источнику; автоматического определения пока нет. Исторические
события с неизвестным типом оборудования также сохраняют NULL.

Сессия различается по `(software_id, module_id, session_id)`. Числовые ID сессий
внутри одного модуля не должны переиспользоваться, пока соответствующие события
остаются в ClickHouse.

### Хранение и доставка

Таблица использует `ReplacingMergeTree(received_at)`, ключ
`(software_id, module_id, id)` и месячную партицию `toYYYYMM(occurred_at)`.
Представления читают `analytics.events_unique` с FINAL и учитывают повтор факта
один раз. DDL находится в `infra/clickhouse/migrations`; запуск:
`docker compose exec api python infra/clickhouse/scripts/update.py`.

`emit_event` выполняет только локальную постановку и не ждёт сеть или свободное
место в очереди. Фоновый отправитель собирает пакеты, ждёт подтверждения записи
и повторяет неудачную доставку с тем же содержимым и токеном вставки.
UUID5 создаётся из источника, модуля, сессии, действия и стабильного `event_key`;
при отсутствии ключа используется UUID4. Время действия не меняется при повторах.

Очередь ограничена количеством событий и байтами. Доставка best effort:
авария/reload, переполнение или исчерпание повторов могут терять события.
Отсутствующий факт не восстанавливается SQL-представлением.

### Викторина

`software_id=1` (LED_PLATFORM); `module_id=1` (QUIZ_IND) — индивидуальная
викторина, `module_id=2` (QUIZ_TEAM) — командная. Режим определяется модулем.
[Требуемые показатели](../interfaces/admin-portal/dashboards.md#индивидуальная-викторина).

| event_id | Действие | Payload |
|---|---|---|
| 1 | SESSION_STARTED | participant_count, team_count, participants[{participant_id,user_id}], teams[{team_id,participant_count}] |
| 2 | PARTICIPANT_JOINED | participant_id, team_id |
| 3 | ANSWER_EVALUATED | session_question_id, participant_id, team_id, is_correct |
| 4 | SESSION_FINISHED | duration_ms, finish_reason |

Количество участников и непустых команд фиксируется на старте. Повторное
подключение не создаёт регистрации. Ответ оценивается при раскрытии вопроса;
командный ответ учитывается один раз от команды. Неотвеченные вопросы не входят
в процент ошибок. Тексты, сложность, тип, варианты, ответы и баллы не отправляются.
Завершение определяется переходом сессии в `FINISHED` и записью `finished_at`
через `/finish`. Для этого события `finish_reason="completed"`: пропуски вопросов,
число обработанных ответов и позиция в игре на завершённость не влияют.
Без события окончания сессия не считается завершённой. Отдельный счётчик
обработанных вопросов для аналитики не ведётся.
`duration_ms` включает паузы, при неизвестном старте — null. Уникальные пользователи
считаются по ненулевым user_id, это не оценка числа людей без идентификации.

Представления: quiz_sessions, quiz_answers, quiz_teams, quiz_participants.
Соединения используют software_id, module_id и session_id. Признак completed
в quiz_sessions определяется наличием finished_at, а не значением finish_reason.
Период дашборда
выбирает игры по started_at; границы дат — Europe/Moscow.
Правильность — correct/evaluated; завершённость — completed/started.
Средняя длительность и её распределение — только completed с известным временем.
Нулевой знаменатель — null. Без окончания игра не объявляется автоматически прерванной.

Подключение и развёртывание: [ClickHouse и Metabase](../subsystems/analytics/clickhouse-metabase.md).
