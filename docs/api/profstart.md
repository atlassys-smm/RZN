# ПрофСтарт — целевой API

Проектируемый контракт трёх тестов: solomin, holland, dellinger. Все URL ниже имеют префикс /api. [OpenAPI](openapi.yaml) · [Сущности](../entities/test.md) · [Методики](../subsystems/profstart/methods.md).

## Общие правила

test_type_id — тип, test_id — версия. Все ID integer int64; в результатах и карточках test_code_type содержит solomin, holland или dellinger. Во всех вопросах type=single_choice; ответ — один answer_option_id.

Контекст владельца определяется сервером, включая гостя. Клиент не присылает user_id при старте или ответе. Чужая сессия в пользовательском контуре — 404; CMS требует права редактирования, аналитика — права просмотра. 401 — нет контекста, 403 — нет административного права.

## CMS

Черновик существует только у теста: published_at=null. У групп/вопросов нет отдельных состояний или методов публикации. Все операции редактируют состав неопубликованного теста; опубликованные версии сохраняются неизменяемыми.

| Метод | URL без /api | Назначение |
|---|---|---|
| GET | `/cms/profstart/test-types` | Каталог трёх типов |
| GET | `/cms/profstart/tests` | Версии тестов |
| POST | `/cms/profstart/tests` | Создать черновик версии |
| GET | `/cms/profstart/tests/{test_id}` | Карточка версии |
| PATCH | `/cms/profstart/tests/{test_id}` | Изменить черновик |
| DELETE | `/cms/profstart/tests/{test_id}` | Удалить черновик |
| POST | `/cms/profstart/tests/{test_id}/copy` | Копировать в новую версию |
| POST | `/cms/profstart/tests/{test_id}/validate` | Проверить готовность публикации |
| POST | `/cms/profstart/tests/{test_id}/publish` | Опубликовать версию |
| GET | `/cms/profstart/tests/{test_id}/groups` | Группы версии |
| POST | `/cms/profstart/tests/{test_id}/groups` | Создать группу |
| GET | `/cms/profstart/tests/{test_id}/groups/{group_id}` | Группа результата |
| PATCH | `/cms/profstart/tests/{test_id}/groups/{group_id}` | Изменить группу |
| DELETE | `/cms/profstart/tests/{test_id}/groups/{group_id}` | Удалить несвязанную группу |
| GET | `/cms/profstart/tests/{test_id}/groups/{group_id}/professions` | Профессии группы |
| POST | `/cms/profstart/tests/{test_id}/groups/{group_id}/professions` | Привязать профессию |
| PATCH | `/cms/profstart/tests/{test_id}/groups/{group_id}/professions/{profession_id}` | Изменить коэффициент связи |
| DELETE | `/cms/profstart/tests/{test_id}/groups/{group_id}/professions/{profession_id}` | Отвязать профессию |
| GET | `/cms/profstart/tests/{test_id}/questions` | Вопросы с вариантами и их весами |
| POST | `/cms/profstart/tests/{test_id}/questions` | Создать вопрос |
| GET | `/cms/profstart/tests/{test_id}/questions/{question_id}` | Вопрос с ключом |
| PATCH | `/cms/profstart/tests/{test_id}/questions/{question_id}` | Изменить вопрос |
| DELETE | `/cms/profstart/tests/{test_id}/questions/{question_id}` | Удалить вопрос с вариантами |
| PUT | `/cms/profstart/tests/{test_id}/questions/order` | Задать порядок всех вопросов |
| GET | `/cms/profstart/tests/{test_id}/questions/{question_id}/options` | Варианты вопроса с весами |
| POST | `/cms/profstart/tests/{test_id}/questions/{question_id}/options` | Создать вариант с группой и весом |
| GET | `/cms/profstart/tests/{test_id}/questions/{question_id}/options/{option_id}` | Вариант и ключ |
| PATCH | `/cms/profstart/tests/{test_id}/questions/{question_id}/options/{option_id}` | Изменить вариант, группу и вес |
| DELETE | `/cms/profstart/tests/{test_id}/questions/{question_id}/options/{option_id}` | Удалить вариант и его вес |

Создание теста назначает номер версии и published_at=null. /validate возвращает 200 с valid=false и errors для неполного состава. /publish проверяет весь тест и устанавливает дату; неполный банк — 422. Повтор публикации возвращает тот же тест.

Для новых стартов используется опубликованная версия с наибольшим version внутри типа. Старые версии сохраняются для истории и начатых сессий. /copy создаёт новый тест с собственными ID вложенных записей; отдельного архивирования нет.

Удаление группы с вариантами или профессиями — 409. Удаление вопроса удаляет варианты; отвязка профессии не удаляет Profession. /questions/order принимает полный массив question_ids без повторов и назначает порядок 1..N атомарно.

### Вопрос и вариант

```json
{"type":"single_choice","axis":"want","text":"Утверждение из банка Соломина","media_id":null,"order":1}
```

```json
{"text":"3","value":3,"media_id":null,"order":4,"group_id":21,"weight":3}
```

group_id и weight — непосредственные поля варианта, изменяются его обычным PATCH. Ось берётся из вопроса. У Соломина четыре варианта с весами 0–3 и равным value; у Голланда шесть действий с весом 1; у Деллингер пять изображений с весом 1. Тип вопроса одинаков. Группа должна принадлежать той же версии.

Связь с профессией:

```json
{"profession_id":17,"coefficient":1}
```

Профессии Соломина необходимы связи subject и labor в одном тесте. Все фигуры связываются с профессиями одинаково. Если связей нет, рекомендаций для группы нет.

## Пользователь

| Метод | URL без /api | Назначение |
|---|---|---|
| GET | `/profstart/tests` | Доступные опубликованные тесты |
| GET | `/profstart/tests/{test_id}` | Инструкция опубликованного теста |
| POST | `/profstart/sessions` | Начать отдельное прохождение |
| GET | `/profstart/sessions/{id}` | Состояние своего прохождения |
| GET | `/profstart/sessions/{id}/questions` | Фиксированные вопросы сессии без ключа |
| POST | `/profstart/sessions/{id}/answer` | Сохранить один ответ |
| POST | `/profstart/sessions/{id}/complete` | Завершить и рассчитать результат |
| POST | `/profstart/sessions/{id}/abandon` | Прервать без результата |
| GET | `/profstart/sessions/{id}/result` | Сохранённый результат своей сессии |
| GET | `/profstart/me/results` | История своих результатов |

/tests возвращает последние опубликованные версии, без ключей. age_group_id фильтрует доступность, test_type_id выбирает методику. Без возрастного фильтра возвращаются все доступные типы, возраст проверяется при старте.

```json
{"test_id":12,"age_group_id":2}
```

Если age_group_ids теста непустой, age_group_id обязателен и входит в список. Для теста без возрастного ограничения достаточно test_id. Источник и тип интерфейса не передаются.

Сессия содержит test_id, test_type_id, test_code_type, test_version, user_id, age_group_id, status, прогресс, принятые ответы, next_question_id, started_at, completed_at и result_id. Для закрытой сессии next_question_id=null. При прерывании status=abandoned, completed_at=null; отдельной даты прерывания нет.

/questions выдаёт фиксированные вопросы и варианты без group_id/weight. Числа шкалы и картинки — представление одного single_choice. Для картинки используется существующий File API.

```json
{"question_id":101,"answer_option_id":404,"time_spent_ms":5200}
```

Принимается следующий неотвеченный вопрос. Повтор того же варианта возвращает сохранённый ответ и текущий прогресс без начисления. Другой вариант уже отвеченного вопроса/нарушение порядка/новый ответ в закрытой сессии — 409; чужой вариант — 422.

Последний ответ даёт ready_to_complete=true; клиент вызывает /complete без тела. Сервер проверяет полноту и атомарно фиксирует результат. Повтор completed возвращает его. /abandon завершает in_progress без результата; повтор abandoned допустим. /complete после abandoned и /abandon после completed — 409.

Результат содержит id, session_id, test_id, test_type_id, user_id, test_code_type, test_version, age_group_id, полноту, дату, scores и professions. Название читается из ресурса теста при необходимости, не дублируется в результате.

scores — все 14/6/5 показателей, включая нули: группа, category, axis, raw_score, max_score, normalized_score, rank, is_leading. professions — уникальные профессии, score/position и reasons с группами, коэффициентами и числовыми вкладами. [Формулы](../subsystems/profstart/results.md). Дополнительные признаки качества не сохраняются.

Таймаут экрана задаётся клиентом киоска. Скрытие не удаляет историю; после авторизации гостя данные остаются у того же User.

## Аналитика

| Метод | URL без /api | Назначение |
|---|---|---|
| GET | `/analytics/profstart/sessions` | Прохождения для аналитики |
| GET | `/analytics/profstart/results` | Результаты пользователей для аналитики |
| GET | `/analytics/profstart/results/{result_id}` | Детальный результат пользователя |
| GET | `/analytics/profstart/summary` | Агрегаты одного типа и версии |

Списки используют limit (50 по умолчанию, максимум 100), offset (0 по умолчанию). Ответ: items, total, limit, offset. Вопросы/варианты/группы: order ASC, id ASC; связи: profession_id ASC; тесты и результаты: created_at DESC, id DESC; сессии: started_at DESC, id DESC.

CMS-список тестов фильтруется по test_type_id и is_draft: true означает published_at=null, false — заполненную дату. is_draft является параметром запроса, не отдельным столбцом.

Аналитические списки: test_type_id, test_id, user_id, age_group_id, date_from, date_to; для сессий также status. История владельца не принимает произвольный user_id. Источник и интерфейс не сохраняются и не фильтруются. Несоответствие test_id и test_type_id — 422.

Даты ISO 8601 с часовым поясом; интервал [date_from,date_to), неверный интервал — 422. Список сессий выбирается по started_at, список результатов — по created_at результата. Фильтры AND. Ответы пользователей, имена и контакты не выдаются.

/summary требует тип и версию; дополнительно фильтруется возраст и период. Период выбирает started_at когорты сессий, результаты — только completed этой когорты. Поля: started_count, in_progress_count, completed_count, abandoned_count, unique_user_count, completion_rate, mean_completed_duration_ms, result_count, groups, professions.

Процент завершения = completed/started ×100. Нулевой знаменатель — null. Повтор увеличивает число сессий, не уникальных пользователей. groups содержит средние и доли ведущих по группе/оси; нули включены, все равные ведущие учтены. professions содержит частоты и средний score только по результатам с этой профессией. При пустой когорте счётчики нулевые, средние/доли null, groups содержит все шкалы, professions=[].

## Согласованность

Проверки владельца, ссылки на версию, статуса сессии, даты публикации теста и уникальности выполняются атомарно. Ошибка расчёта откатывает завершение: completed без результата не допускается. Error имеет code, message и массив details; конфликт — 409, неверные параметры/ключ — 422.
