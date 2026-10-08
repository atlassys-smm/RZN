# Рекомендации пользователя

Общий профиль принадлежит User, включая гостя, и предназначен для источников разных модулей. ПрофСтарт добавляет один неизменяемый источник на завершённый тип. Новый источник уточняет существующий профиль; изменение весов пересчитывает его из сохранённых снимков. История отдельных тестов не меняется.

## UserRecommendation

Таблица `user_recommendations`. Уникальность user_id: один профиль на пользователя.

| Поле | Тип | Описание |
|---|---|---|
| `id` | bigint | PK |
| `user_id` | bigint | Уникальный FK → users.id |
| `weights` | jsonb | Конфигурация источников: source_code, weight; ПрофСтарт также сохраняет test_type_id и test_code_type |
| `created_at` | timestamp UTC | Создание профиля |
| `updated_at` | timestamp UTC | Последнее обновление рейтинга |

## UserRecommendationSource

Таблица `user_recommendation_sources`. Уникальность (recommendation_id, source_code). Источник неизменяем после успешного завершения; API записи для клиента отсутствует.

| Поле | Тип | Описание |
|---|---|---|
| `id` | bigint | PK |
| `recommendation_id` | bigint | FK → user_recommendations.id |
| `source_code` | string | Пространство модуля и тип: profstart.solomin, profstart.holland, profstart.dellinger |
| `source_reference` | jsonb | Ссылка на исходный результат: result_id, test_id, test_type_id, test_code_type, test_version, result_created_at |
| `weight` | decimal | Исходный вес; при расчёте применяется текущая настройка weights профиля |
| `group_scores` | jsonb | Все показатели групп, включая нулевые: group_id/code/name, category, raw_score, max_score, normalized_score, rank, is_leading |
| `profession_scores` | jsonb | Полный снимок соответствия профессиям: profession_id/name, score, position, reasons с группами и коэффициентами |
| `created_at` | timestamp UTC | Создание источника |

Внутри JSON десятичные значения сохраняются строками для точности. Типизированные поля score, weight и contribution API возвращает числами; структура reasons зависит от поставщика источника. Нулевой вес не препятствует сохранению источника. Исторический TestResult ссылается на источник уникальным обязательным recommendation_source_id. Связи group_id и profession_id внутри JSON — снимки, а не внешние ключи; сервис проверяет их при создании. Основные коды групп защищены.

Для нового источника ПрофСтарта учитываются все группы с положительным вкладом, включая неведущие. После переноса существующих результатов снимки сохраняют ранее рассчитанное соответствие профессиям без переинтерпретации истории.

## UserRecommendationProfession

Таблица `user_recommendation_professions`. Изменяемый текущий рейтинг, максимум три записи на профиль. Уникальны (recommendation_id, profession_id) и (recommendation_id, position).

| Поле | Тип | Описание |
|---|---|---|
| `id` | bigint | PK |
| `recommendation_id` | bigint | FK → user_recommendations.id |
| `profession_id` | bigint | FK → professions.id |
| `profession_name` | string | Название из снимка источника |
| `position` | integer | Позиция 1–3 |
| `score` | decimal(5,2) | Итоговое соответствие 0–100 |
| `contributions` | jsonb | Вклады источников: source_id, source_code, weight, effective_weight_percent, test_score, contribution, reasons |

Рейтинг сортируется по score DESC, profession_id ASC. Сохраняются только положительные округлённые баллы существующих профессий; набор может быть короче трёх или пустым. При неполном наборе источников веса нормируются по имеющимся источникам с положительным весом. Источник без данной профессии участвует с нулевым вкладом. Округление — Decimal ROUND_HALF_UP до двух знаков после суммирования точных взвешенных вкладов.

[API](../api/user-recommendations.md) · [Расчёт ПрофСтарта](../subsystems/profstart/results.md).
