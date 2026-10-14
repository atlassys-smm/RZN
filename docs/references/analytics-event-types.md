# Типы событий аналитики

В `event_id` передаётся числовой код `EventType(IntEnum)`; UUID конкретного факта
находится в поле `id`. Параметры действия — в `payload` события
[AnalyticsEvent](../entities/analytics.md). Перечисления определены в
`app/services/analytics/enums.py`.

## Действия

| event_id | EventType | Описание |
|---|---|---|
| 1 | SESSION_STARTED | Фактический переход в активную сессию |
| 2 | PARTICIPANT_JOINED | Новый зарегистрированный участник |
| 3 | ANSWER_EVALUATED | Правильность оценённого ответа участника или команды |
| 4 | SESSION_FINISHED | Окончание, причина и длительность |

## Модули

| module_id | ModuleType | Модуль |
|---|---|---|
| 1 | QUIZ_IND | Индивидуальная викторина |
| 2 | QUIZ_TEAM | Командная викторина |
| 3 | VIDEO_SCENARIO | Профессии в действии |
| 4 | PROFSTART | ПрофСтарт |
| 5 | FEEDBACK | Обратная связь |
| 6 | PROFESSION_AVATAR | Аватар профессий |
| 7 | TREE_OF_PROFESSIONS | Древо профессий |
| 8 | REGIONAL_MAP | Интерактивная карта региона |
| 9 | PROFBATTLE | Профбаттл |
| 10 | VIDEO_WINDOWS | Видео-окна |
| 11 | VIDEO_RESUME | Видео-резюме |
| 12 | SCREENSAVER | Заставка |

Коды 0 не используются; опубликованные значения не перенумеровываются.
Сейчас отправляются четыре действия модулей QUIZ_IND и QUIZ_TEAM с
`software_id=1` (LED_PLATFORM). Остальные модули определены в справочнике,
но ещё не отправляют события. Новые действия добавляются при подключении источника.
Payload и правила подсчёта — в [AnalyticsEvent → Викторина](../entities/analytics.md#викторина).
