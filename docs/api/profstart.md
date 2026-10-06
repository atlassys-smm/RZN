# ПрофСтарт — целевой API

Проектируемый контракт расширяемого каталога типов; итоговый расчёт поддерживает solomin, holland, dellinger. Все URL ниже имеют префикс /api. [OpenAPI](openapi.yaml) · [Сущности](../entities/test.md) · [Методики](../subsystems/profstart/methods.md).

## Общие правила

test_type_id — тип, test_id — версия. Все ID integer int64; в CMS-карточке test_code_type содержит код любого типа; в результатах и пользовательском контуре — только solomin, holland или dellinger. Во всех вопросах type=single_choice; ответ — один answer_option_id.

Контекст владельца определяется сервером, включая гостя. Клиент не присылает user_id при старте или ответе. Чужая сессия в пользовательском контуре — 404; CMS требует права редактирования, аналитика — права просмотра. 401 — нет контекста, 403 — нет административного права.

## CMS

Типы можно добавлять через POST /cms/profstart/test-types. code — уникальная строка латиницей в нижнем регистре, цифрами и подчёркиванием, начинается с буквы (1–64 символа), после создания неизменяем. PATCH меняет name и description. DELETE типа с активным тестом запрещён: 409 type_in_use; ссылки остальных тестов также защищены FK, каскадного удаления истории нет. Проверка удаления и активация теста согласованы атомарно. Тип без связанных тестов удаляется с 204.

```json
{"code":"new_type","name":"Новый тип теста","description":"Описание"}
```

Новые типы можно наполнить и активировать в CMS. Итоговые результаты и рекомендации пока рассчитываются только по solomin, holland, dellinger. Для типа без алгоритма /complete и /analytics/profstart/summary возвращают 422 unsupported_test_type; нулевые результаты вместо неподдерживаемого алгоритма не создаются.

Тест имеет status=draft, active или archived. Черновик существует только у теста: status=draft, published_at=null. У групп/вопросов нет отдельных состояний или методов публикации. Состав редактируется только у draft; active и archived неизменяемы.

| Метод | URL без /api | Назначение |
|---|---|---|
| GET | `/cms/profstart/test-types` | Каталог типов тестов |
| POST | `/cms/profstart/test-types` | Создать тип теста |
| GET | `/cms/profstart/tests` | Версии тестов |
| POST | `/cms/profstart/tests` | Создать черновик версии |
| GET | `/cms/profstart/tests/{test_id}` | Карточка версии |
| PATCH | `/cms/profstart/tests/{test_id}` | Изменить черновик |
| DELETE | `/cms/profstart/tests/{test_id}` | Удалить черновик |
| POST | `/cms/profstart/tests/{test_id}/copy` | Копировать в новую версию |
| POST | `/cms/profstart/tests/{test_id}/validate` | Проверить готовность публикации |
| POST | `/cms/profstart/tests/{test_id}/publish` | Опубликовать и активировать тест |
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
| GET | `/cms/profstart/test-types/{test_type_id}` | Карточка типа теста |
| PATCH | `/cms/profstart/test-types/{test_type_id}` | Изменить название и описание типа |
| DELETE | `/cms/profstart/test-types/{test_type_id}` | Удалить неиспользуемый тип |
| POST | `/cms/profstart/tests/{test_id}/archive` | Архивировать активный тест |

Создание теста любого существующего типа назначает номер версии, status=draft и published_at=null. /validate возвращает 200 с valid=false и errors для неполного состава. /publish проверяет draft, переводит его в active и заполняет published_at; неполный банк — 422. Для Соломина требуется ровно 42 вопроса: по 3 на каждую из 7 групп и осей want/can, максимум 9. Для Голланда — ровно 15 вопросов, максимум 15; для Деллингер — один вопрос. Для нового типа проверяется общая целостность, scale_maxima=[]; алгоритм расчёта не появляется автоматически.

Не более одного active на test_type_id. /publish атомарно архивирует предыдущий active и активирует draft; конкурентные публикации согласованы блокировкой типа и частичным уникальным индексом. /archive переводит active в archived без замены. Повтор /publish для active и /archive для archived возвращает прежнюю запись; /publish для archived и /archive для draft — 409. /copy любой версии создаёт новый draft с собственными ID состава. Начатые сессии продолжают и завершают прежнюю версию после архивирования. published_at сохраняет дату первой активации у active/archived.

Удаление группы с вариантами или профессиями — 409. Удаление вопроса удаляет варианты; отвязка профессии не удаляет Profession. /questions/order принимает полный массив question_ids без повторов и назначает порядок 1..N атомарно.

Вложенные ID в URL проверяются как цепочка принадлежности: test_id → group_id/question_id → profession_id/option_id. Чужой ресурс в этой цепочке — 404; group_id в теле варианта из другой версии — 422. Все изменения состава и публикация используют общую блокировку теста: нельзя записать изменение после перехода в active. /copy переводит ссылки вариантов и связей профессий на новые ID групп/вопросов, сохраняя внешние profession_id и media_id.

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
| GET | `/profstart/tests` | Доступные активные тесты |
| GET | `/profstart/tests/{test_id}` | Карточка теста для старта или своей истории |
| POST | `/profstart/sessions` | Начать отдельное прохождение |
| GET | `/profstart/sessions/{id}` | Состояние своего прохождения |
| GET | `/profstart/sessions/{id}/questions` | Фиксированные вопросы сессии без ключа |
| POST | `/profstart/sessions/{id}/answer` | Сохранить один ответ |
| POST | `/profstart/sessions/{id}/complete` | Завершить и рассчитать результат |
| POST | `/profstart/sessions/{id}/abandon` | Прервать без результата |
| GET | `/profstart/sessions/{id}/result` | Сохранённый результат своей сессии |
| GET | `/profstart/me/results` | История своих результатов |

/tests возвращает только active-тесты кодов solomin, holland, dellinger, без ключей. Новые типы без алгоритма в пользовательский каталог не входят; прямое получение инструкции или старт — 422 unsupported_test_type, без создания сессии. Старт неактивного теста — 409 test_not_active. age_group_id фильтрует доступность, test_type_id выбирает методику. Без возрастного фильтра возвращаются все доступные типы, возраст проверяется при старте.

```json
{"test_id":12,"age_group_id":2}
```

GET /profstart/tests/{test_id} возвращает status карточки. Активная карточка доступна для инструкции; архивная — только владельцу существующей сессии этого test_id в любом статусе. Название теста для истории читается из этой карточки. Draft и архивная версия без своей сессии — 409 test_not_active; неизвестный ID — 404. Просмотр архивной карточки не разрешает новый старт.

Если age_group_ids теста непустой, age_group_id обязателен и входит в список. Для теста без возрастного ограничения достаточно test_id. Источник и тип интерфейса не передаются.

Сессия содержит test_id, test_type_id, test_code_type, test_version, user_id, age_group_id, status, прогресс, принятые ответы, next_question_id, started_at, completed_at и result_id. Для закрытой сессии next_question_id=null. При прерывании status=abandoned, completed_at=null; отдельной даты прерывания нет.

/questions выдаёт фиксированные вопросы и варианты без group_id/weight. Числа шкалы и картинки — представление одного single_choice. Для картинки используется существующий File API.

```json
{"question_id":101,"answer_option_id":404,"time_spent_ms":5200}
```

Принимается следующий неотвеченный вопрос. Повтор того же варианта возвращает сохранённый ответ и текущий прогресс без начисления. Другой вариант уже отвеченного вопроса/нарушение порядка/новый ответ в закрытой сессии — 409; чужой вариант — 422.

Последний ответ даёт ready_to_complete=true только в in_progress. При повторе ответа в completed/abandoned значение false, next_question_id=null; сохранённые answered_at и time_spent_ms не меняются. Для всех повторов возвращается текущий прогресс сессии. Клиент читает /sessions/{id}, если требуется восстановить её окончательный статус. Если ready_to_complete=true, клиент вызывает /complete без тела. Сервер проверяет полноту и атомарно фиксирует результат. Повтор completed возвращает его. /abandon завершает in_progress без результата; повтор abandoned допустим. /complete после abandoned и /abandon после completed — 409.

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

CMS-список тестов фильтруется по test_type_id и status=draft/active/archived. Каталог типов GET /cms/profstart/test-types возвращает массив всех типов, включая новые, в порядке id ASC, без пагинации. Остальные CMS-списки и списки аналитики/истории используют описанную пагинацию.

Аналитические списки: test_type_id, test_id, user_id, age_group_id, date_from, date_to; для сессий также status. История владельца не принимает произвольный user_id. Источник и интерфейс не сохраняются и не фильтруются. Несоответствие test_id и test_type_id — 422.

Даты ISO 8601 с часовым поясом; интервал [date_from,date_to), неверный интервал — 422. Список сессий выбирается по started_at, список результатов — по created_at результата. Фильтры AND. Исходные ответы, имена и контакты участников в аналитических списках не выдаются.

/summary требует тип и опубликованную версию (active или archived); для draft — 409 test_not_published. Дополнительно фильтруется возраст и период. Период выбирает started_at когорты сессий, результаты — только completed этой когорты. Поля: started_count, in_progress_count, completed_count, abandoned_count, unique_user_count, completion_rate, mean_completed_duration_ms, result_count, groups, professions.

Процент завершения = completed/started ×100. Нулевой знаменатель — null. Повтор увеличивает число сессий, не уникальных пользователей. groups содержит средние и доли ведущих по группе/оси; нули включены, все равные ведущие учтены. professions содержит частоты и средний score только по результатам с этой профессией. При пустой когорте счётчики нулевые, средние/доли null, groups содержит все шкалы, professions=[].

Результаты содержат ровно 14/6/5 уникальных пар (group_id, axis); пустой scores не допускается. Для completed обязательны полный набор ответов, completed_at и result_id. У in_progress/abandoned оба поля null; answered_count не превышает question_count. Согласованность массива answers, порядка и next_question_id проверяется сервером.

mean_completed_duration_ms рассчитывается по серверным completed_at − started_at, в миллисекундах; у незавершённых сессий duration_ms=null. recommended_percent = recommended_count/result_count ×100, где result_count — все результаты выбранной когорты. В агрегате profession_name читается из текущего Profession; отдельные результаты сохраняют прежние снимки названий.

## Согласованность

Проверки владельца, ссылки на версию, статуса сессии, активности теста при старте и уникальности выполняются атомарно. Ошибка расчёта откатывает завершение: completed без результата не допускается. Error имеет code, message и массив details; конфликт — 409, неверные параметры/ключ — 422.
