# WebSocket API

WebSocket-эндпоинты для получения уведомлений об изменениях в реальном времени.

Клиент подключается к WebSocket, получает уведомление о событии и загружает актуальные данные через REST API.

---

## Викторина

### Подключение

```
ws://host/api/v1/quiz/sessions/{sessionId}/ws
```

### События от сервера

| Событие | Описание | Что загружать |
|---------|----------|---------------|
| `session_state` | Полное состояние сессии | — (данные уже в событии) |
| `question_started` | Начался приём ответов | `GET /quiz/sessions/{id}` |
| `votes_update` | Обновление голосов | `GET /quiz/sessions/{id}` |
| `question_revealed` | Правильный ответ показан | `GET /quiz/sessions/{id}` |
| `round_finished` | Раунд завершён | `GET /quiz/sessions/{id}/results/rounds/{index}` |
| `session_finished` | Сессия завершена | — |

### Формат событий

```json
{ "type": "votes_update" }
{ "type": "question_revealed" }
{ "type": "round_finished", "data": { "round_index": 0 } }
```

---

## Профессии в действии

### Подключение

```
ws://host/api/v1/interactive-video/sessions/{sessionId}/ws
```

### События от сервера

**Для LED-экрана:**

| Событие | Описание | Что загружать |
|---------|----------|---------------|
| `phase_changed` | Сменилась фаза (playing → waiting → result) | `GET /state` |
| `votes_updated` | Поступил новый голос | `GET /state` |
| `scenario_finished` | Сценарий завершён, переход к следующему | `GET /state` |
| `session_finished` | Показ завершён | — |

**Для мобильного клиента:**

| Событие | Описание | Что загружать |
|---------|----------|---------------|
| `phase_changed` | Сменилась фаза (waiting → result) | `GET /voting` |
| `scenario_finished` | Сценарий завершён | `GET /voting` |
| `session_finished` | Показ завершён | — |

Мобильному клиенту не нужен `votes_updated` — он уже проголосовал и ждёт результат.

### Формат событий

```json
{ "type": "phase_changed" }
{ "type": "votes_updated" }
{ "type": "scenario_finished" }
{ "type": "session_finished" }
```

### Фазы показа

| Фаза | Описание |
|------|----------|
| `playing` | Проигрывание ролика |
| `waiting` | Точка голосования, сбор ответов |
| `result` | Показ результата |

---

## Пример использования

1. Клиент подключается к WebSocket
2. Загружает начальное состояние через REST API
3. Получает событие `{ "type": "votes_updated" }`
4. Загружает обновлённое состояние через REST API
5. Обновляет отображение
