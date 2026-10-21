# Организации

Описание сущности для справочника организаций (учебные заведения и работодатели).

---

## Organization (Организация)

Единый справочник организаций. Используется в ПАК «Интерактивная карта региона» и аналитике.

### Атрибуты

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer (int64, автоинкремент) | Уникальный идентификатор |
| `name` | string | Название организации |
| `type` | integer (OrganizationType) | `1` — работодатель, `2` — учебное заведение |
| `full_name` | text, nullable | Полное название |
| `location` | text, nullable | Населённый пункт или территория |
| `industry_branch_id` | integer (int64), nullable | FK → `industry_branches.id`; индустрия определяется через отрасль |
| `employee_count` | integer, nullable | Численность работников |
| `scale_or_product` | text, nullable | Масштаб деятельности или продукция |
| `practice_info` | text, nullable | Практика и наставничество |
| `education_level` | string, nullable | Уровень учебного заведения |
| `deleted_at` | timestamp with time zone, nullable | Отметка удаления |
| `address` | text, nullable | Адрес |
| `coordinates` | json, nullable | Координаты на карте (широта, долгота) |
| `description` | text, nullable | Описание |
| `website` | string, nullable | URL сайта |
| `phone` | string, nullable | Контактный телефон |
| `created_at` | timestamp | Дата создания |
| `updated_at` | timestamp | Дата обновления |

### Где используется

- **ПАК «Интерактивная карта региона»** — отображение на карте
- **Аналитика** — рейтинг организаций по интересам/просмотрам
- **Цифровой профиль** — выбранные организации в профиле

---

## Связанные разделы

- **API:** `/organizations` — публичный API, `/organizations` (POST/PUT/DELETE) — CMS

## EducationProgram (Направление подготовки)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer (int64, автоинкремент) | Идентификатор |
| `name` | string | Название направления подготовки |
| `education_level` | string | Уровень образования |
| `duration` | string | Срок обучения, включая текстовые пояснения |
| `base_class` | string, nullable | База приёма |
| `organization_id` | integer (int64) | FK → `organizations.id`, учебное заведение типа `2` |
| `created_at` | timestamp with time zone | Дата создания |
| `updated_at` | timestamp with time zone | Дата изменения |
| `deleted_at` | timestamp with time zone, nullable | Отметка удаления |

Название направления не уникально: одинаковая программа может быть у разных учебных заведений.
Направления подготовки доступны через CRUD `/organizations/education-programs`. Все справочные API исключают удалённые записи.

## API справочников и мягкое удаление

| Ресурс | Запросы |
|--------|---------|
| `/organizations` | GET списка, POST; `/organizations/{id}`: GET, PUT, DELETE |
| `/organizations/education-programs` | GET списка, POST; `/organizations/education-programs/{id}`: GET, PUT, DELETE |

GET доступны публично; POST/PUT/DELETE — редактору контента и администратору. Все новые сведения из JSON доступны в ответах и запросах изменения. Пропущенные поля PUT сохраняются, явный null очищает nullable-поля.

Удалённые строки не попадают в списки и total; GET/PUT/DELETE по удалённому ID возвращают 404. Новые ссылки проверяются на доступность и тип организации. Удаление профессии, работодателя или программы помечает их связи удалёнными. Индустрию, направление, отрасль или учебное заведение с активными зависимостями удалить нельзя (409). Повторный POST удалённой пары восстанавливает её с тем же ID; изменение на уже существующую пару возвращает 409.
