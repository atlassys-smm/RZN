# Игровая сессия

Описание сущностей для проведения игровых сессий на LED-платформе.

Игровая сессия — это факт проведения игры или викторины. В зависимости от режима сессия может быть:
- **Индивидуальная викторина** (`mode = individual`) — вопросы с вариантами ответов, все участники отвечают индивидуально, рейтинг по `individual_score`
- **Командная игра** (`mode = team`) — профориентационная игра с формированием команд, раундами заданий, обсуждениями и рейтингом команд

Используется в сценариях: **Индивидуальная викторина**, **Командная работа**.

→ [GameQuestion и GameAnswerOption](quiz.md) | [Шаблоны сценариев](scenario-template.md) | [CMS: Викторина](../subsystems/cms/quiz.md)

---

## GameSession (Игровая сессия)

Факт проведения игры или викторины. При создании сессия заполняется раундами и вопросами (из шаблона или вручную оператором) — снапшоты хранятся в `GameSessionRound` и `GameSessionQuestion`.

### Атрибуты

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор сессии |
| `mode` | enum | Режим: `individual` (индивидуальная викторина), `team` (командная игра) |
| `status` | enum | Статус: `waiting` (формирование команд), `active` (идёт игра), `finished` (завершена) |
| `current_round_index` | integer | Индекс текущего раунда (для восстановления после сбоя) |
| `current_question_index` | integer | Индекс текущего вопроса в раунде (для восстановления после сбоя) |
| `settings` | json | Настройки сессии — см. ниже. Включая `team_count` для mode=team |
| `created_at` | timestamp | Дата создания |
| `finished_at` | timestamp, nullable | Дата завершения |

### settings (JSON)

| Поле | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `team_count` | integer | — | Количество команд (для mode=team, от 2 до 8) |
| `auto_reveal` | boolean | `true` | Автоматический показ правильного ответа по истечении времени на вопрос. Если `false` — оператор нажимает «Показать ответ» на планшете |
| `auto_next` | boolean | `false` | Автоматический переход к следующему вопросу после показа ответа |
| `auto_next_delay` | integer | `5` | Задержка автоперехода в секундах |
| `between_rounds_delay` | integer | `10` | Пауза между раундами в секундах (экран результатов раунда) |
| `show_intermediate_results` | boolean | `true` | Показывать промежуточный рейтинг после каждого раунда |

Время на ответ берётся из `GameQuestion.time_limit` (у каждого вопроса своё).

### Связи

- **GameSession → GameSessionRound**: сессия имеет множество раундов (снапшоты)
- **GameSession → GameSessionTeam**: сессия имеет множество команд (для режима `team`)
- **GameSession → GameSessionParticipant**: сессия имеет множество участников

### Где используется

- **LED-медиаплатформа** — проведение сессий
- **Аналитика** — анализ результатов сессий

---

## GameSessionRound (Раунд сессии)

Снапшот раунда, заполненный при создании сессии из шаблона или вручную оператором.

### Атрибуты

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор |
| `session_id` | integer (int64) | ID сессии |
| `round_type` | enum | Тип раунда из [справочника](../references/scenario-round-types.md): `quick_start`, `tools`, `skills`, `situation`, `team_building`, `process`, `future`, `regional`, `final` |
| `order` | integer | Порядок раунда в сессии |

### Связи

- **GameSessionRound → GameSession**: раунд принадлежит одной сессии
- **GameSessionRound → GameSessionQuestion**: раунд имеет множество вопросов

---

## GameSessionQuestion (Вопрос в раунде сессии)

Снапшот вопроса, закреплённого за раундом сессии.

### Атрибуты

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор |
| `round_id` | integer (int64) | ID раунда сессии |
| `question_id` | integer (int64) | ID исходного вопроса ([GameQuestion](quiz.md)) |
| `order` | integer | Порядок вопроса в раунде |

### Связи

- **GameSessionQuestion → GameSessionRound**: вопрос принадлежит одному раунду
- **GameSessionQuestion → GameQuestion**: ссылка на исходный вопрос (текст, варианты, время, баллы)
- **GameSessionQuestion → GameSessionAnswer**: вопрос имеет множество ответов

---

## GameSessionTeam (Команда в сессии)

Команда, участвующая в командной игре. Создаётся автоматически при создании сессии (по `team_count`).

Используется только для сессий с `mode = team`.

### Атрибуты

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор команды |
| `session_id` | integer (int64) | ID сессии |
| `name` | string | Название команды |
| `color` | string | Цвет команды (для визуального различия) |
| `captain_id` | integer (int64), nullable | ID капитана команды (ссылка на GameSessionParticipant) |
| `score` | integer | Итоговый счёт команды |
| `created_at` | timestamp | Дата создания |

### Связи

- **GameSessionTeam → GameSession**: команда принадлежит одной сессии
- **GameSessionTeam → GameSessionParticipant**: капитан команды и множество участников

### Примечания

- Состав команды — от 2 до 10 человек
- В сессии может быть от 2 до 8 команд
- Капитан — первый подключившийся к команде; может передать роль; при отключении — случайный; оператор может сменить

---

## GameSessionParticipant (Участник сессии)

Участник игровой сессии. Может быть авторизованным пользователем или гостем.

### Атрибуты

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор |
| `session_id` | integer (int64) | ID сессии |
| `team_id` | integer (int64), nullable | ID команды (null для индивидуальной викторины) |
| `user_id` | integer (int64), nullable | ID пользователя (null для гостя) |
| `individual_score` | integer | Индивидуальный счёт участника |
| `joined_at` | timestamp | Дата подключения к сессии |

### Связи

- **GameSessionParticipant → GameSession**: участник принадлежит одной сессии
- **GameSessionParticipant → GameSessionTeam**: участник может принадлежать команде
- **GameSessionParticipant → User**: участник привязан к пользователю (nullable)

### Примечания

- Для индивидуальной викторины `team_id` = null
- Капитан определяется через `GameSessionTeam.captain_id`, не через роль участника

---

## GameSessionAnswer (Ответ в сессии)

Факт ответа на вопрос в рамках сессии. Хранится в БД для аналитики и истории.

### Атрибуты

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор |
| `session_id` | integer (int64) | ID сессии |
| `session_question_id` | integer (int64) | ID вопроса в сессии (GameSessionQuestion) |
| `participant_id` | integer (int64) | ID участника, давшего ответ (капитан для команды, или индивидуальный участник) |
| `team_id` | integer (int64), nullable | ID команды (для team mode) |
| `answer` | json | Ответ — структура зависит от типа вопроса |
| `is_correct` | boolean | Правильность ответа |
| `score` | integer | Начисленные баллы |
| `created_at` | timestamp | Дата ответа |

### Связи

- **GameSessionAnswer → GameSession**: ответ в рамках сессии
- **GameSessionAnswer → GameSessionQuestion**: ответ на конкретный вопрос
- **GameSessionAnswer → GameSessionParticipant**: кто ответил
- **GameSessionAnswer → GameSessionTeam**: какая команда (для team mode)

### Где используется

- **Аналитика** — анализ результатов, статистика правильных ответов
- **Результаты** — формирование рейтингов по раундам и итогового

---

## Состояние активной сессии (Redis)

Горячее состояние текущей игры. При сбое восстанавливается из БД (`current_round_index`, `current_question_index`), таймер сбрасывается.

| Ключ | Тип | Описание |
|------|-----|----------|
| `session:{id}:timer_remaining` | integer | Секунд осталось на текущий вопрос |
| `session:{id}:timer_running` | boolean | Идёт ли отсчёт |
| `session:{id}:timer_updated_at` | timestamp | Когда последний раз обновили |
| `session:{id}:votes` | hash | `{participant_id → vote}` — голоса текущего вопроса |
| `session:{id}:revealed` | boolean | Правильный ответ уже показан |

### Логика таймера

- **Старт вопроса**: `remaining = question.time_limit`, `running = true`, `updated_at = now`
- **Пауза**: `remaining = remaining - (now - updated_at)`, `running = false`
- **Возобновление**: `updated_at = now`, `running = true`
- **Клиент вычисляет**: если `running` → `remaining - (now - updated_at)`, иначе → `remaining`

---

## Особенности режимов

### Индивидуальная викторина

- `mode = individual`
- Оператор выбирает шаблон сценария или настраивает раунды вручную (от 3 до 8 типов)
- Каждый участник отвечает персонально через `answer`
- `GameSessionTeam` не создаётся
- Рейтинг формируется по `individual_score`

### Командная игра

- `mode = team`
- Команды создаются автоматически при создании сессии (`team_count`)
- Участники подключаются к команде через `team/{teamId}/join`
- Участники голосуют через `vote`, капитан отправляет итоговый ответ через `answer`
- Рейтинг формируется по `GameSessionTeam.score`

→ [Шаблоны сценариев](scenario-template.md) | [CMS: Викторина](../subsystems/cms/quiz.md)
