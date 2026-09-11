# Материалы по регистрации и профилю

!!! success "Материал готов"

---

## Модель регистрации

Единая запись `User` — пользователь создаётся при первом сканировании QR-кода. В зависимости от наличия OAuth-данных он находится в гостевом или авторизованном состоянии.

- **Гость** — `status = guest`, есть `guest_id`, нет OAuth-данных
- **Авторизованный** — `status = active`, заполнены OAuth-поля

Результаты всех активностей всегда привязаны к `id` пользователя. При переходе из гостевого режима в авторизованный **перенос данных не требуется**.

Провайдеры OAuth:
- **Яндекс ID** — имя, email, аватар, дата рождения
- **VK ID** — имя, email, аватар, пол, дата рождения

Для сотрудников системы (StaffUser) используется отдельная модель — email/пароль с ролями.

---

## 1. Маршрут пользователя (User Flow)

```mermaid
flowchart TD
    QR["QR-код на терминале"] --> CheckAuth{"Есть активный\ntoken в браузере?"}

    CheckAuth -->|"Да"| KnownUser["Узнаём User по token"]
    KnownUser --> Activity["Прохождение активности"]
    Activity --> Profile["Профиль"]

    CheckAuth -->|"Нет"| Choice["Экран выбора:\nВойти через OAuth\nили продолжить как гость?\n+ чекбокс согласия"]

    Choice -->|"OAuth + галочка"| OAuth["Авторизация у провайдера"]
    OAuth --> CreateUserActive["Создание User\n(status=active, OAuth-поля)"]
    CreateUserActive --> Activity

    Choice -->|"Гость"| CreateUserGuest["Создание User\n(status=guest, guest_id)"]
    CreateUserGuest --> Activity
```

### Ключевые решения

- При сканировании QR проверяется **наличие токена** в браузере
- Если токен есть — пользователь узнаётся, **новая запись не создаётся**
- Если токена нет — **экран выбора**: авторизоваться через OAuth или продолжить как гость
- При выборе OAuth → создание User со `status = active`, принятие согласия
- При выборе гостя → создание User со `status = guest`, `guest_id`
- Результаты всегда привязаны к `id` — **перенос не нужен**
- Гость может авторизоваться позже (в течение 24ч) — OAuth-поля заполнятся у той же записи
- Гость видит предложение авторизоваться **на каждой странице** личного кабинета

---

## 2. Sequence-схема входа

### Сценарий 1: Авторизованный пользователь (есть токен)

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant Browser as Браузер (телефон)
    participant Terminal as Терминал
    participant Auth as Auth-сервис
    participant DB as База данных

    Terminal-->>User: QR-код (URL с session_id)
    User->>Browser: Сканирует QR → открывает URL
    Browser->>Auth: GET /qr/scan?session_id=xxx&token=yyy
    Auth->>Auth: Проверка токена
    Auth->>DB: Поиск User по user_id из токена
    DB-->>Auth: User (status=active)
    Auth->>Terminal: Уведомление: User подключился
    Auth-->>Browser: User идентифицирован, переход в активность
    Terminal-->>User: Пользователь подключён к сессии
```

### Сценарий 2: Первый контакт — выбор OAuth

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant Browser as Браузер (телефон)
    participant Terminal as Терминал
    participant Auth as Auth-сервис
    participant OAuth as OAuth-провайдер
    participant DB as База данных

    Terminal-->>User: QR-код (URL с session_id)
    User->>Browser: Сканирует QR → открывает URL
    Browser->>Auth: GET /qr/scan?session_id=xxx (без токена)
    Auth-->>Browser: URL экрана выбора
    Browser-->>User: Экран выбора + чекбокс согласия

    User->>Browser: Галочка поставлена → выбор OAuth-провайдера
    Browser->>Auth: GET /authorize?session_id=xxx (согласие подтверждено)
    Auth->>DB: Запись ConsentAcceptance
    Auth-->>Browser: Редирект на OAuth
    User->>OAuth: Авторизация у провайдера
    OAuth-->>Auth: Callback с кодом
    Auth->>OAuth: Обмен кода на данные
    OAuth-->>Auth: Данные пользователя

    Auth->>DB: Создание User (status=active, OAuth-поля)
    DB-->>Auth: User создан
    Auth->>Terminal: Уведомление: User подключился

    Auth-->>Browser: Выдача JWT (access + refresh)
    Browser-->>User: Переход в активность
```

### Сценарий 3: Первый контакт — выбор «Гость»

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant Browser as Браузер (телефон)
    participant Terminal as Терминал
    participant Auth as Auth-сервис
    participant DB as База данных

    Terminal-->>User: QR-код (URL с session_id)
    User->>Browser: Сканирует QR → открывает URL
    Browser->>Auth: GET /qr/scan?session_id=xxx (без токена)
    Auth-->>Browser: URL экрана выбора
    Browser-->>User: Экран выбора + чекбокс согласия

    User->>Browser: Галочка поставлена → выбор «Продолжить как гость»
    Browser->>Auth: POST /qr/scan/guest?session_id=xxx (согласие подтверждено)
    Auth->>DB: Запись ConsentAcceptance + создание User (status=guest, guest_id, guest_expires_at)
    DB-->>Auth: User создан
    Auth->>Terminal: Уведомление: гость подключился
    Auth-->>Browser: guest_id + JWT гостя
    Browser-->>User: guest_id в localStorage
    Note over User,DB: Результаты привязываются к id этого User
```

### Сценарий 4: Гость авторизуется позже (в течение 24ч)

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant Browser as Браузер (телефон)
    participant Auth as Auth-сервис
    participant OAuth as OAuth-провайдер
    participant DB as База данных

    Note over User,DB: Гость активен (guest_id в localStorage, status=guest)

    User->>Browser: Баннер «Авторизуйтесь» + чекбокс согласия
    User->>Browser: Галочка поставлена → нажимает «Войти через OAuth»
    Browser->>Auth: GET /authorize?guest_id=xxx (согласие подтверждено)
    Auth->>DB: Запись ConsentAcceptance
    Auth-->>Browser: Редирект на OAuth
    User->>OAuth: Авторизация у провайдера
    OAuth-->>Auth: Callback с кодом
    Auth->>OAuth: Обмен кода на данные
    OAuth-->>Auth: Данные пользователя

    Auth->>DB: Поиск User по guest_id
    DB-->>Auth: Найден User (status=guest)

    Auth->>DB: Обновление: oauth_provider, oauth_provider_id,<br/>email, name, avatar, status=active
    DB-->>Auth: User обновлён

    Auth-->>Browser: Выдача JWT (access + refresh)
    Browser-->>User: Профиль (данные уже привязаны)
```

---

## 3. Состояния учётной записи

### Пользователь (User)

```mermaid
flowchart TD
    Start["Первый контакт\n(QR-код)"] --> Guest["GUEST\n• guest_id сгенерирован\n• guest_expires_at = 24ч\n• Результаты привязаны к id"]
    
    Guest -->|"OAuth в течение 24ч"| Active["ACTIVE\n• OAuth-поля заполнены\n• guest_expires_at обнулён\n• Полный доступ к профилю"]
    
    Guest -->|"24 часа прошли\nбез авторизации"| Anonymized["ANONYMIZED\n• Гостевая сессия разорвана\n• Данные обезличены\n• Аналитика сохранена"]
    
    Active -->|"Действие администратора"| Deactivated["DEACTIVATED\n• Вход заблокирован\n• Данные сохранены"]
    
    Anonymized -.->|"Может создать\nнового гостя"| Guest
```

**Описание состояний:**

| Статус | Описание | Как попадает |
|--------|----------|--------------|
| `guest` | Гостевой режим, есть `guest_id`, 24 часа на авторизацию | Первый контакт (QR-код), выбор «Продолжить как гость» |
| `active` | Авторизован через OAuth, полноценный пользователь | Авторизация через OAuth в течение 24ч |
| `anonymized` | Гость не авторизовался, данные обезличены | Автоматически через 24ч после создания гостя |
| `deactivated` | Деактивирован администратором | Действие администратора |

**Обезличивание:** если гость не авторизовался в течение 24 часов, гостевая сессия разрывается, связь с гостем утеряна навсегда. Результаты и аналитика сохраняются, но привязаны к `id` записи без возможности восстановления личности.

---

## 4. Интерфейсные экраны

### Экран 1: Терминал — QR-код для входа

**Где отображается:** большой LED-экран, интерактивная панель

**Содержание:**
- Заголовок: «Сканируйте QR-код для участия»
- Крупный QR-код в центре экрана
- Пояснение: «Наведите камеру телефона на QR-код»
- URL для ручного ввода (на случай, если камера не работает)

---

### Экран 2: Телефон — выбор способа входа

**Где отображается:** мобильное устройство пользователя (после сканирования QR)

**Содержание:**
- Заголовок: «Как вы хотите продолжить?»
- Кнопка «Войти через Яндекс ID» (логотип + текст)
- Кнопка «Войти через VK ID» (логотип + текст)
- Кнопка «Продолжить как гость» (менее выделенная)
- Чекбокс «Я принимаю условия [согласия на обработку персональных данных](../entities/consent.md)» (обязательный)
- Пояснение: «Авторизация через Яндекс или VK — быстро и безопасно»

---

### Экран 3: Телефон — личный кабинет (авторизованный)

**Где отображается:** мобильное устройство, веб-портал (PWA), доступен после входа через OAuth

**Содержание:** в соответствии с [интерфейсом личного кабинета пользователя](../interfaces/mobile-client/index.md)

---

### Экран 4: Телефон — личный кабинет (гость)

**Где отображается:** мобильное устройство, веб-портал (PWA), доступен после выбора «Продолжить как гость»

**Содержание профиля:** в соответствии с [интерфейсом личного кабинета](../interfaces/mobile-client/index.md) (гостевой режим)

**Баннер предложения авторизации:**

Блок в контенте или плавающий блок. Содержит:
- Текст: «Авторизуйтесь для полного доступа. Ваши результаты уже сохранены.»
- Кнопка «Авторизоваться» → переход на экран выбора способа входа (без кнопки «Продолжить как гость», вместо неё — «Отмена» для возврата в гостевой профиль)

---

## Требования

- **Формат:** PDF/SVG/PNG
- Пользовательская схема (маршрут)
- Sequence-схема входа
- Основные состояния учётной записи
- Не менее 4 интерфейсных экранов регистрации/входа/профиля

