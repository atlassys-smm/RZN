# Аналитика

Описание сущности для событий аналитики.

---

## AnalyticsEvent (Событие аналитики)

Единое событие для аналитики. Собирается со всех подсистем и используется для консолидированной аналитики, дашбордов и отчётов.

### Атрибуты

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор события (используется для идемпотентности) |
| `device_type` | string | Тип оборудования (например, `avatar_terminal`, `led_screen`, `pwa`) — см. [Источники событий](../references/event-sources.md) |
| `software_id` | string | Программный комплекс (например, `led_platform`, `profstart`, `feedback`) — см. [Источники событий](../references/event-sources.md) |
| `session_id` | integer (int64), nullable | ID локальной сессии на терминале (от авторизации до выхода) |
| `user_id` | integer (int64) | ID пользователя (гостя или авторизованного) — всегда заполнен |
| `payload` | json | Дополнительные параметры события (action_type, entity_type, entity_id, result, duration, content_version и другие данные) |
| `created_at` | timestamp | Дата и время события |

### Структура payload

Поле `payload` содержит произвольные данные события, которые зависят от типа события. Примеры:

```json
{
  "action_type": "user_action",
  "entity_type": "profession",
  "entity_id": "uuid-profession-123",
  "result": "selected",
  "duration": 45000,
  "content_version": "1.2"
}
```

| Поле в payload | Тип | Описание |
|----------------|-----|----------|
| `action_type` | enum | Тип действия: `user_action`, `system_action` |
| `entity_type` | string | Тип сущности: `profession`, `industry`, `direction`, `employer`, `educational_institution`, `question`, `survey` |
| `entity_id` | integer (int64) | ID сущности |
| `result` | string | Результат: `correct`, `incorrect`, `completed`, `viewed`, `selected`, `recommended` |
| `duration` | integer | Длительность в миллисекундах |
| `content_version` | string | Версия контента |

### Связи

- **AnalyticsEvent → User**: событие привязано к пользователю (`user_id`) — гостю или авторизованному
- **AnalyticsEvent → Profession**: событие может быть связано с профессией (через `entity_id` и `entity_type`)
- **AnalyticsEvent → Direction**: событие может быть связано с направлением (через `entity_id` и `entity_type`)

### Где используется

- **LED-медиаплатформа** — отправка событий о сессиях, ответах, результатах
- **ПрофСтарт** — отправка событий о прохождении теста, результатах
- **Командная игра** — отправка событий о раундах, ответах команд
- **Обратная связь** — отправка событий о прохождении анкет
- **Аватар профессий** — отправка событий о генерации фото
- **Видео-окна** — отправка событий о просмотре видео
- **Видео-резюме** — отправка событий о записи видео
- **Аналитика** — приём, хранение, агрегация событий
- **Цифровой профиль** — анализ событий для формирования рекомендательной модели (агрегируемое значение)

### Примечания

- Приём событий идемпотентный: повторная передача с тем же `id` не приводит к двойному учёту
- Производительность: не менее 100 000 событий/сутки, не менее 10 000 000 событий в хранилище
- События хранятся в раздельных слоях: сырые события, нормализованные данные, агрегаты
- Срок хранения — настраиваемый, по умолчанию 36 месяцев

### Примеры типов событий

| Тип события | Описание | software_id |
|-------------|----------|-------------|
| `session_started` | Начало сессии | `led_platform` |
| `session_completed` | Завершение сессии | `led_platform` |
| `quiz_answer` | Ответ на вопрос викторины | `led_platform` |
| `test_started` | Начало теста | `profstart` |
| `test_completed` | Завершение теста | `profstart` |
| `test_answer` | Ответ на вопрос теста | `profstart` |
| `team_game_round_started` | Начало раунда командной игры | `led_platform` |
| `team_game_answer` | Ответ команды | `led_platform` |
| `survey_submitted` | Отправка анкеты | `feedback` |
| `avatar_generated` | Генерация фото в образе профессии | `profession_avatar` |
| `video_viewed` | Просмотр видео о профессии | `video_windows` |
| `video_resume_recorded` | Запись видео-резюме | `video_resume` |
| `profession_viewed` | Просмотр карточки профессии | `led_platform`, `profstart` |
| `career_route_generated` | Формирование рекомендаций | `profstart` |
