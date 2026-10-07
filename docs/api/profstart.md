# ПрофСтарт — API

Контракт расширяемого каталога типов; итоговый расчёт поддерживает solomin, holland, dellinger. Все URL ниже имеют префикс /api. [OpenAPI](openapi.yaml) · [Сущности](../entities/test.md) · [Методики](../subsystems/profstart/methods.md).

## Общие правила

test_type_id — тип, test_id — версия. Все ID integer int64; в CMS-карточке test_code_type содержит код любого типа; в результатах и пользовательском контуре — только solomin, holland или dellinger. Во всех вопросах type=single_choice; ответ — один answer_option_id.

Контекст владельца определяется сервером по пользовательскому Bearer-токену, включая гостя. Клиент не присылает user_id при старте или ответе. Чужая сессия в пользовательском контуре — 404; отсутствие контекста — 401. CMS-маршруты следуют существующей архитектуре CMS проекта: отдельная проверка токена и административных прав в backend пока отсутствует.

## CMS

Типы можно добавлять через POST /cms/profstart/test-types. code — уникальная строка латиницей в нижнем регистре, цифрами и подчёркиванием, начинается с буквы (1–64 символа). PATCH меняет name и description, в том числе при наличии активного теста. Код дополнительного типа можно изменить только без связанных тестов; коды solomin, holland, dellinger фиксированы. Недопустимая смена кода — 409; дубликат — 409. Проверка ссылок и смена кода атомарны и согласованы с созданием тестов. DELETE типа с активным тестом запрещён: 409; ссылки остальных тестов также защищены FK, каскадного удаления истории нет. Проверка удаления и активация теста согласованы атомарно. Тип без связанных тестов удаляется с 204.

```json
{"code":"new_type","name":"Новый тип теста","description":"Описание"}
```

Новые типы можно наполнить и активировать в CMS. Итоговые результаты и рекомендации пока рассчитываются только по solomin, holland, dellinger. Для типа без алгоритма расчёт в /answer возвращает 422; нулевые результаты вместо неподдерживаемого алгоритма не создаются.

Влияние на общий подбор задаётся в test_types.recommendation_weight_percent: целый процент 0–100, стандарт solomin=40, holland=40, dellinger=20. Сумма весов поддерживаемых типов — ровно 100; 0 отключает влияние типа, сохраняя возможность отдельного прохождения. У новых типов без алгоритма вес по умолчанию 0 и положительное значение запрещено: 422.

Проценты доступны в карточке и каталоге типов. Перераспределение сохраняется атомарным PUT /cms/profstart/test-types/recommendation-weights с полным набором solomin/holland/dellinger. PATCH одного типа также проверяет итоговую сумму; нарушение — 422. Для переноса процента между типами используется PUT всей тройки. Настройка изменяется и при активных тестах; сохранённые результаты отдельных тестов остаются прежними, общий подбор использует текущие веса. Тип с ненулевым весом удалить нельзя: 409; сначала требуется перераспределить проценты. Изменения и проверка суммы согласованы общей блокировкой конфигурации, включая создание/удаление типов. Конкурентные PUT сохраняют целый набор; смешение значений разных запросов запрещено.

```json
{"solomin":40,"holland":40,"dellinger":20}
```

PUT возвращает обновлённые записи TestType с recommendation_weight_percent; фиксированный URL регистрируется до /test-types/{test_type_id}.

Тест имеет status=1 (draft), active или archived. Черновик существует только у теста: status=1 (draft), published_at=null. У групп/вопросов нет отдельных состояний или методов публикации. Состав редактируется только у draft; active и archived неизменяемы.

| Метод | URL без /api | Назначение |
|---|---|---|
| GET | `/cms/profstart/test-types` | Каталог типов тестов |
| POST | `/cms/profstart/test-types` | Создать тип теста |
| PUT | `/cms/profstart/test-types/recommendation-weights` | Атомарно настроить веса трёх типов |
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
| PATCH | `/cms/profstart/test-types/{test_type_id}` | Изменить тип теста |
| DELETE | `/cms/profstart/test-types/{test_type_id}` | Удалить неиспользуемый тип |
| POST | `/cms/profstart/tests/{test_id}/archive` | Архивировать активный тест |

Создание теста любого существующего типа назначает номер версии, status=1 (draft) и published_at=null. /validate возвращает 200 с valid=false и errors для неполного состава. /publish проверяет draft, переводит его в active и заполняет published_at; неполный банк — 422. Для Соломина требуется ровно 42 вопроса: по 3 на каждую из 7 групп и блоков want/can; общий максимум — 18 на группу. scale_maxima возвращает по одному объекту group_id/max_score на группу, без axis. Для Голланда — ровно 15 вопросов, максимум 15; для Деллингер — один вопрос. Для нового типа проверяется общая целостность, scale_maxima=[]; алгоритм расчёта не появляется автоматически.

Не более одного active на test_type_id. /publish атомарно архивирует предыдущий active и активирует draft; конкурентные публикации согласованы блокировкой типа и частичным уникальным индексом. /archive переводит active в archived без замены. Повтор /publish для active и /archive для archived возвращает прежнюю запись; /publish для archived и /archive для draft — 409. /copy любой версии создаёт новый draft с собственными ID состава. Начатые сессии продолжают и завершают прежнюю версию после архивирования. published_at сохраняет дату первой активации у active/archived.

Удаление группы с вариантами или профессиями — 409. Удаление вопроса удаляет варианты; отвязка профессии не удаляет Profession. /questions/order принимает полный массив question_ids без повторов и назначает порядок 1..N атомарно.

Вложенные ID в URL проверяются как цепочка принадлежности: test_id → group_id/question_id → profession_id/option_id. Чужой ресурс в этой цепочке — 404; group_id в теле варианта из другой версии — 422. Все изменения состава и публикация используют общую блокировку теста: нельзя записать изменение после перехода в active. /copy переводит ссылки вариантов и связей профессий на новые ID групп/вопросов, сохраняя внешние profession_id и media_id.

### Вопрос и вариант

Полные тексты, варианты и ключи начального состава представлены в [банке вопросов](../subsystems/profstart/questions/index.md).

Создание и PATCH вопросов/вариантов принимают multipart/form-data. Каждое поле — отдельная часть формы, а не JSON-тело. Пример полей вопроса без вложения:

```text
type=single_choice
axis=want
text=Мне интересно помогать человеку освоить то, что у него пока не получается.
order=1
```

Поля варианта Соломина:

```text
text=3 — Полностью согласен
value=3
order=4
group_id=21
weight=3
```

Файл передаётся бинарной частью file; необязательное превью — file_preview (JPEG, PNG, WebP или GIF), название/описание нового файла — file_title/file_description. Для видео без превью сервер извлекает первый кадр; для остальных файлов автоматического превью нет. file_preview без нового file — 422. Без нового file при PATCH прежний файл и его метаданные сохраняются; file_title/file_description применяются только к новому вложению. media_id не принимается. У Голланда и Деллингер value не передаётся, в ответе value=null.

CMS и пользовательский API возвращают в вопросах/вариантах file: объект url, preview_url, mime_type, title, description либо null. Подписанные ссылки действуют 24 часа; повторное чтение ресурса выдаёт свежие ссылки. В БД остаётся внутренний media_id, в том числе при /copy. Файл и сущность сохраняются в одной транзакции, старые файлы сохраняются для копий и истории. [Файлы](../entities/files.md).

group_id и weight — непосредственные поля варианта, изменяются его обычным PATCH. Блок определяется вопросом; want и can Соломина суммируются по группе. У Соломина четыре варианта с весами 0–3 и равным value; у Голланда шесть действий с весом 1; у Деллингер пять изображений с весом 1. Тип вопроса одинаков. Группа должна принадлежать той же версии.

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
| POST | `/profstart/sessions/{id}/abandon` | Прервать без результата |
| GET | `/profstart/sessions/{id}/result` | Сохранённый результат своей сессии |
| GET | `/profstart/me/results` | История своих результатов |
| GET | `/profstart/me/recommendations` | Общий рейтинг профессий по результатам тестов |

/tests возвращает только active-тесты кодов solomin, holland, dellinger, без ключей. Новые типы без алгоритма в пользовательский каталог не входят; прямое получение инструкции или старт — 422, без создания сессии. Старт неактивного теста — 409. age_group_id фильтрует доступность, test_type_id выбирает методику. Без возрастного фильтра возвращаются все доступные типы, возраст проверяется при старте.

```json
{"test_id":12,"age_group_id":2}
```

GET /profstart/tests/{test_id} возвращает status карточки. Активная карточка доступна для инструкции; архивная — только владельцу существующей сессии этого test_id в любом статусе. Название теста для истории читается из этой карточки. Draft и архивная версия без своей сессии — 409; неизвестный ID — 404. Просмотр архивной карточки не разрешает новый старт.

Если age_group_ids теста непустой, age_group_id обязателен и входит в список. Для теста без возрастного ограничения достаточно test_id. Источник и тип интерфейса не передаются.

Сессия содержит test_id, test_type_id, test_code_type, test_version, user_id, age_group_id, status, прогресс, принятые ответы, next_question_id, started_at, completed_at и result_id. Для закрытой сессии next_question_id=null. При прерывании status=3 (abandoned), completed_at=null; отдельной даты прерывания нет.

/questions выдаёт фиксированные вопросы и варианты без group_id/weight. Числа шкалы и картинки — представление одного single_choice. Картинки передаются объектом file с подписанными ссылками существующего File API.

```json
{"question_id":101,"answer_option_id":404,"time_spent_ms":5200}
```

time_spent_ms — неотрицательное целое число миллисекунд. Принимается следующий неотвеченный вопрос. Повтор того же варианта возвращает сохранённый ответ и текущий прогресс без начисления. Другой вариант уже отвеченного вопроса/нарушение порядка/новый ответ в закрытой сессии — 409; чужой вариант — 422.

Последний ответ автоматически завершает прохождение: /answer атомарно сохраняет ответ, результат, показатели групп и рекомендации и устанавливает status=2 (completed). Подтверждение содержит текущий status: 1 — in_progress, 2 — completed, 3 — abandoned. Результат в ответ /answer не включается: после status=2 клиент вызывает GET /sessions/{id}/result. При ошибке расчёта последний ответ и результат откатываются вместе. Повтор ранее принятого того же варианта возвращает сохранённые answered_at и time_spent_ms, текущий прогресс без повторного расчёта. Сохранённый результат завершённой сессии не меняется. next_question_id=null у закрытой сессии. /abandon прерывает in_progress без результата; повтор abandoned допустим, а /abandon после completed — 409. После восстановления соединения клиент читает /sessions/{id} и /sessions/{id}/result.

Результат содержит id, session_id, test_id, test_type_id, user_id, test_code_type, test_version, age_group_id, полноту, дату, scores и professions. Название читается из ресурса теста при необходимости, не дублируется в результате.

scores — все 7/6/5 показателей, включая нули: группа, category, raw_score, max_score, normalized_score, rank, is_leading. У Соломина raw_score суммирует оба блока want и can, max_score=18; axis в scores и reasons не передаётся. professions — уникальные профессии, score/position и reasons с группами, коэффициентами и числовыми вкладами. [Формулы](../subsystems/profstart/results.md). Дополнительные признаки качества не сохраняются.

Таймаут экрана задаётся клиентом киоска. Скрытие не удаляет историю; после авторизации гостя данные остаются у того же User.

## Общий подбор профессий

GET /profstart/me/recommendations возвращает вычисляемый общий рейтинг текущего владельца, без параметров user_id, фильтров, пагинации и клиентских весов. Контекст гостя поддерживается. Ответ: calculated_at, is_complete, available_weight_percent, weights, results, missing_test_types, professions. results содержит по одному последнему завершённому результату каждого типа с положительным весом, включая архивные версии. professions содержит profession_id/name, score, position и contributions по каждому выбранному результату: test_type_id, test_code_type, result_id, recommendation_weight_percent, effective_weight_percent, test_score, contribution.

Стандартный общий score = round_half_up(0.4*S + 0.4*H + 0.2*D, 2). При неполном наборе делитель — сумма весов пройденных типов; отсутствие профессии в результате пройденного теста даёт нулевой вклад, а не исключение веса. Без результатов — 200, available_weight_percent=0, results=[], professions=[], is_complete=false. is_complete=true требует результатов всех типов с положительным настроенным весом; missing_test_types перечисляет недостающие. Общая выдача использует текущие настройки, отдельно в БД не сохраняется и не меняет историю отдельных результатов. [Подробные правила и округление](../subsystems/profstart/results.md#общий-подбор-по-трём-тестам).

## Списки и фильтры

Списки используют limit (50 по умолчанию, максимум 100), offset (0 по умолчанию). Ответ: items, total, limit, offset. Вопросы/варианты/группы: order ASC, id ASC; связи: profession_id ASC; тесты и результаты: created_at DESC, id DESC.

CMS-список тестов фильтруется по test_type_id и status=1 (draft)/active/archived. Каталог типов GET /cms/profstart/test-types возвращает массив всех типов, включая новые, в порядке id ASC, без пагинации. Остальные CMS-списки и история используют описанную пагинацию.

История владельца фильтруется по test_type_id, test_id, date_from и date_to; произвольный user_id не принимает. Несоответствие test_id и test_type_id — 422. Даты ISO 8601 с часовым поясом; интервал [date_from,date_to), неверный интервал — 422. Период выбирает created_at результата; фильтры AND.

Результаты содержат ровно 7/6/5 уникальных group_id; пустой scores не допускается. Для completed обязательны полный набор ответов, completed_at и result_id. У in_progress/abandoned оба поля null; answered_count не превышает question_count. Согласованность массива answers, порядка и next_question_id проверяется сервером.

## Согласованность

Проверки владельца, ссылки на версию, статуса сессии, активности теста при старте и уникальности выполняются атомарно. Ошибка расчёта откатывает завершение: completed без результата не допускается. Ошибки оформляются стандартным HTTPException: поле detail содержит сообщение или список ошибок состава теста. FastAPI возвращает ошибки типов и обязательных полей в detail со стандартными loc, msg и type. Конфликт — 409, неверные параметры/ключ — 422.

ID в запросах объявлены как int без отдельных проверок числовых границ. Неизвестные query-параметры игнорируются, как в остальных разделах API: переданный user_id не меняет владельца. В PATCH null необязательных полей с обязательным значением игнорируется; nullable value варианта допускает очистку.


Поле `status` передаётся числом. Для теста: `1` — draft, `2` — active, `3` — archived; фильтр CMS, например `?status=1`. Для прохождения: `1` — in_progress, `2` — completed, `3` — abandoned. Статус теста меняют `/publish` и `/archive`, статус прохождения — `/answer` после последнего вопроса и `/abandon`.
