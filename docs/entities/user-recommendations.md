# Рекомендации пользователя

Общий профиль принадлежит User, включая гостя, и предназначен для источников разных модулей. ПрофСтарт добавляет один неизменяемый источник на завершённый тип, включая дополнительные типы CMS. Каждый источник содержит показатели групп и профессий; в итоговом рейтинге участвуют только пары source_module/source_code с положительным весом в SOURCE_WEIGHTS. Итоговый рейтинг рассчитывается при каждом запросе из снимков источников и не сохраняется в БД. История отдельных тестов не меняется.

## UserRecommendation

Таблица `user_recommendations`. Уникальность user_id: один профиль на пользователя.

| Поле | Тип | Описание |
|---|---|---|
| `id` | bigint | PK |
| `user_id` | bigint | Уникальный FK → users.id |
| `created_at` | timestamp UTC | Создание профиля |
| `updated_at` | timestamp UTC | Последнее добавление источника |

## UserRecommendationSource

Таблица `user_recommendation_sources`. Уникальность (recommendation_id, source_module, source_code). Индекс (source_module, source_code) поддерживает выборку по модулю и коду. Источник неизменяем после успешного завершения; API записи для клиента отсутствует.

| Поле | Тип | Описание |
|---|---|---|
| `id` | bigint | PK |
| `recommendation_id` | bigint | FK → user_recommendations.id |
| `source_module` | string | Модуль источника: profstart |
| `source_code` | string | Код внутри модуля: solomin, holland, dellinger |
| `source_reference` | jsonb | Ссылка на исходный результат: session_id, test_id, test_type_id, test_code_type, test_version, completed_at |
| `group_scores` | jsonb | Все показатели групп, включая нулевые: group_id/code/name, category, raw_score, max_score, normalized_score, rank, is_leading |
| `profession_scores` | jsonb | Полный снимок соответствия профессиям: profession_id/name, score, position, reasons с группами и их баллами |
| `created_at` | timestamp UTC | Создание источника |

Внутри JSON десятичные значения сохраняются строками для точности. Типизированные поля score, weight и contribution API возвращает числами; структура reasons зависит от поставщика источника. Завершённая сессия любого типа ссылается на источник уникальным recommendation_source_id; для in_progress и abandoned ссылка равна null. Связи group_id и profession_id внутри JSON — снимки, а не внешние ключи; сервис проверяет их при создании. Основные коды групп защищены.

Для источника ПрофСтарта учитываются все группы с положительным вкладом, включая неведущие. Изменения связей профессий и подписей групп в CMS не меняют сохранённые снимки.

## Итоговый рейтинг

Веса источников заданы в `app/models/user_recommendations/weights.py`: ("profstart", "solomin")=40, ("profstart", "holland")=40, ("profstart", "dellinger")=20. В таблицах они не хранятся; CMS их не изменяет. Для новых поставщиков нужно добавить пару модуля и кода и её вес в SOURCE_WEIGHTS. Неизвестная пара имеет нулевое влияние.

GET рассчитывает максимум три профессии, не записывая результат. Рейтинг сортируется по score DESC, profession_id ASC. Возвращаются только положительные округлённые баллы существующих профессий; набор может быть короче трёх или пустым. При неполном наборе веса нормируются по имеющимся источникам с положительным весом. Источник без данной профессии участвует с нулевым вкладом. Источник с весом 0 сохраняется, но не влияет на выдачу. Округление — Decimal ROUND_HALF_UP до двух знаков после суммирования точных взвешенных вкладов.

[API](../api/user-recommendations.md) · [Расчёт ПрофСтарта](../subsystems/profstart/results.md).
