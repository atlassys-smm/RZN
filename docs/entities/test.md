# ПрофСтарт — сущности

Целевая модель расширяемого каталога типов; итоговый расчёт пока поддерживает три предзаданных теста. Таблицы модуля требуют реализации; User, Profession и File уже существуют. ID — integer (int64), веса и баллы — decimal, даты — UTC timestamp. [Методики](../subsystems/profstart/methods.md) · [API](../api/profstart.md).

## TestType — тип теста

Таблица `test_types`, три предзаданные записи и типы, добавляемые CMS.

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор, PK |
| `code` | string | Уникальный неизменяемый код типа; предзаданные solomin, holland, dellinger; новые коды задаются CMS |
| `name` | string | Название |
| `description` | text | Описание |
| `created_at` | timestamp | Дата создания |
| `updated_at` | timestamp | Дата изменения |

CMS создаёт типы, читает каталог и карточки, изменяет name/description и удаляет неиспользуемые типы. code уникален и неизменяем. Удаление типа с active-тестом — 409 type_in_use; ссылки остальных тестов также защищены FK, связанные тесты и историю каскадно не удаляют. Итоговый расчёт поддерживает только solomin, holland, dellinger; новые типы до появления алгоритма недоступны для пользовательского старта.

## ProfStartTest — версия теста

Таблица `profstart_tests`. В API test_id обозначает версию, test_type_id — методику.

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор, PK |
| `test_type_id` | integer (int64) | FK → TestType |
| `version` | integer | Положительный номер внутри типа, назначается сервером |
| `name` | string | Название |
| `description` | text | Описание |
| `instructions` | text | Инструкция перед прохождением |
| `age_group_ids` | json (массив integer int64) | Список допустимых возрастных групп; пустой — без возрастного фильтра |
| `status` | string | draft, active, archived; жизненный цикл только у теста |
| `published_at` | timestamp, nullable | Дата первой активации; null у draft, заполнена у active и archived |
| `created_at` | timestamp | Дата создания |
| `updated_at` | timestamp | Дата изменения |

Уникальность (test_type_id, version). Черновик определяется status=draft; published_at=null до активации. Публикация проверяет весь состав и атомарно переводит draft в active, заполняя published_at. Частичный уникальный индекс (test_type_id) WHERE status='active' допускает не более одного активного теста одного типа. Блокировка записи типа согласует конкурирующие публикации и удаление типа.

Публикация нового draft переводит прежний active этого типа в archived в той же транзакции. /archive переводит active в archived без замены; активного теста может не быть. Начатые сессии продолжают свою версию. Содержимое active и archived неизменяемо, published_at сохраняется. Копирование любой версии создаёт новый draft с published_at=null и собственными ID состава. Повтор /publish для active и /archive для archived идемпотентен; archived не публикуется повторно, draft не архивируется.

## TestGroup — группа результата

Таблица `test_groups`.

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор, PK |
| `test_id` | integer (int64) | FK → ProfStartTest (версия теста) |
| `code` | string | Код группы; уникален внутри версии теста |
| `name` | string | Название |
| `description` | text | Описание |
| `category` | string | subject, labor, riasec, geometry |
| `order` | integer | Порядок отображения |

У группы нет собственного черновика, статуса или публикации. Она входит в состав теста. Уникальность (test_id, code); точный набор 7/6/5 проверяется при публикации трёх поддерживаемых типов. У новых типов состав задаётся CMS. Группы не заменяют Direction. Одна группа Соломина используется на обеих осях.

## TestQuestion — вопрос

Таблица `test_questions`.

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор, PK |
| `test_id` | integer (int64) | FK → ProfStartTest (версия теста) |
| `type` | string | Только single_choice |
| `axis` | string | Ось показателя: want, can, general |
| `text` | text | Текст |
| `media_id` | integer (int64), nullable | ID файла, FK → File; null при отсутствии медиа |
| `order` | integer | Положительный порядок, уникальный внутри теста |
| `created_at` | timestamp | Дата создания |
| `updated_at` | timestamp | Дата изменения |

У вопроса нет собственного черновика, статуса или публикации. Во всех тестах пользователь выбирает один вариант; различаются подписи, количество и изображения. Все вопросы обязательны, набор и порядок фиксированы. Возрастная доступность задаётся тесту.

## TestAnswerOption — вариант с весом

Таблица `test_answer_options`. Группа и вес хранятся непосредственно в варианте.

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор, PK |
| `question_id` | integer (int64) | FK → TestQuestion |
| `text` | text | Подпись варианта, в том числе подпись изображения |
| `media_id` | integer (int64), nullable | ID файла, FK → File; null при отсутствии медиа; изображение обязательно для фигур |
| `value` | integer, nullable | Значение шкалы Соломина: 0, 1, 2, 3; у Голланда/Деллингер null |
| `order` | integer | Порядок, уникальный внутри вопроса |
| `group_id` | integer (int64) | FK → TestGroup той же версии теста |
| `weight` | decimal | Конечное число; Соломин 0–3 и равно value, Голланд/Деллингер — 1 |

Каждый вариант связан с одной группой. Ось расчёта берётся из TestQuestion.axis, отдельно в варианте не дублируется. У предзаданных типов в вопросе 4/6/5 вариантов. Соломин: 42 вопроса (7 групп × 3 вопроса × 2 оси), максимум 9 на группу/ось. Голланд: ровно 15 вопросов, максимум 15 на тип. Деллингер: один вопрос. Ноль — полноценный выбранный ответ; несвязанным группам начисляется нулевой вклад. Отдельной сущности для веса нет, правильных ответов нет.

## TestGroupProfession — связь с профессией

Таблица `test_group_professions`, многие-ко-многим с существующей Profession.

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор, PK |
| `group_id` | integer (int64) | FK → TestGroup той же версии теста |
| `profession_id` | integer (int64) | FK → Profession |
| `coefficient` | decimal | 0 < значение ≤ 1, по умолчанию 1 |

Уникальность (group_id, profession_id). Для профессии Соломина необходимы subject- и labor-группы той же версии. У геометрического теста связь может быть задана для любой фигуры. [Формула рекомендаций](../subsystems/profstart/results.md).

При копировании создаются новые ID групп, вопросов, вариантов и связей, а group_id в вариантах/связях и question_id в вариантах переназначаются на копию. Ссылки на существующие Profession и File сохраняются.

Группы, вопросы, варианты и связи редактируются только как содержимое draft, без отдельного жизненного цикла. Для изменения active или archived копируется весь тест.

## TestSession — прохождение

Таблица `test_sessions`.

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор, PK |
| `test_id` | integer (int64) | FK → ProfStartTest (версия теста) |
| `user_id` | integer (int64) | FK → User, включая гостя |
| `age_group_id` | integer (int64), nullable | Выбранная возрастная группа; null при отсутствии выбора |
| `status` | string | in_progress, completed, abandoned |
| `started_at` | timestamp | Время начала прохождения |
| `completed_at` | timestamp, nullable | Время успешного завершения; null до завершения и у abandoned |
| `created_at` | timestamp | Дата создания |
| `updated_at` | timestamp | Дата изменения |

Сервер проверяет, что answered_count в API равен числу уникальных ответов и не превышает question_count. У completed обязателен полный набор, completed_at и связанный TestResult; у in_progress/abandoned нет результата, completed_at=null. Для закрытой сессии next_question_id=null.

Тип интерфейса и источник не сохраняются. Для прерывания достаточно status=abandoned; completed_at остаётся null. Повторное прохождение создаёт новую сессию. Завершение и запись результата — атомарная операция.

## TestAnswer — ответ пользователя

Таблица `test_answers`.

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор, PK |
| `session_id` | integer (int64) | FK → TestSession |
| `question_id` | integer (int64) | FK → TestQuestion |
| `answer_option_id` | integer (int64) | FK → TestAnswerOption |
| `answered_at` | timestamp | Время записи |
| `time_spent_ms` | integer | Целое ≥ 0, присланное клиентом |

Уникальность (session_id, question_id). Повтор того же варианта не начисляет баллы повторно; другой вариант уже отвеченного вопроса — 409. Принадлежность вопроса и варианта версии проверяется сервером.

## TestResult — результат пользователя

Таблица `test_results`, одна запись на полностью завершённую сессию.

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор, PK |
| `session_id` | integer (int64) | FK → TestSession; уникальный, один результат на сессию |
| `test_id` | integer (int64) | FK → ProfStartTest (версия теста) |
| `user_id` | integer (int64) | FK → User, включая гостя |
| `test_code_type` | string | Сохранённый код solomin, holland или dellinger |
| `test_version` | integer | Номер версии теста |
| `answered_count` | integer | Число принятых ответов; у результата равно question_count |
| `question_count` | integer | Число вопросов версии теста |
| `created_at` | timestamp | Время окончательного расчёта |

Название теста при необходимости читается из ProfStartTest по test_id; в результате не дублируется. Результат окончательный, собственного черновика нет. Дополнительные признаки качества не хранятся. Для чтения названия архивного теста пользователь обращается к его карточке; доступ разрешён владельцу существующей сессии этой версии.

## TestResultScore — показатель группы

Таблица `test_result_scores`.

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор, PK |
| `result_id` | integer (int64) | FK → TestResult |
| `group_id` | integer (int64) | FK → TestGroup той же версии теста |
| `axis` | string | Ось показателя: want, can, general |
| `group_code` | string | Снимок кода группы |
| `group_name` | string | Снимок названия группы |
| `category` | string | Снимок категории группы: subject, labor, riasec, geometry |
| `raw_score` | decimal | Сумма весов выбранных вариантов |
| `max_score` | decimal | Достижимый максимум по группе и оси |
| `normalized_score` | decimal | Показатель 0–100, округлённый до двух знаков |
| `rank` | integer | Место внутри категории и оси |
| `is_leading` | boolean | Признак положительного максимума в категории и оси |

Уникальность (result_id, group_id, axis). Все показатели, включая нулевые, сохраняются: 14/6/5.

## TestResultProfession — сохранённая рекомендация

Таблица `test_result_professions`.

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор, PK |
| `result_id` | integer (int64) | FK → TestResult |
| `profession_id` | integer (int64) | FK → Profession |
| `profession_name` | string | Снимок названия профессии |
| `score` | decimal | Балл рекомендации 0–100, два знака |
| `position` | integer | Позиция в отсортированном списке |
| `reasons` | json (массив объектов) | JSON-массив групп, использованных в формуле: group_id/code/name, axis, normalized_score, coefficient, contribution до усреднения |

Уникальность (result_id, profession_id). Сохраняются группы и числовые вклады без отдельного текста пояснения связи. Изменения каталога не пересчитывают историю; удаление связанных профессий блокируется ссылочной целостностью.
