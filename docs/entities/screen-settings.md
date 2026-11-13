# Настройки экрана

Общий набор настроек в таблице `screen_settings`: единственная запись без `id` и первичного ключа.
В БД поля именуются в snake_case, в API — в camelCase. Описания настроек в БД не хранятся.

| Поле | По умолчанию |
|------|-------------|
| `carouselDurationSec` | 15 |
| `selectedCardHoldSec` | 1 |
| `cardExpandDurationSec` | 0.8 |
| `victoryDisplayDurationSec` | 3 |
| `screensaversPerCycle` | 4 |
| `initialBackgroundDurationSec` | 10 |
| `betweenScreensaversDurationSec` | 5 |
| `screensaverRouletteWaitSec` | 3 |
| `analyticsDurationSec` | 60 |
| `professionIntroBackgroundSec` | 2 |
| `professionFirstCountdownSec` | 15 |
| `professionNextSpinDelaySec` | 3 |

`GET /api/cms/led/settings` возвращает все 12 значений.
`PUT /api/cms/led/settings` принимает JSON с изменяемыми значениями и возвращает полный набор.
Пропущенные поля сохраняются, пустой объект допустим. Чтение и обновление не используют идентификатор.
Длительности — конечные числа >= 0; `screensaversPerCycle` — целое >= 1.
`null`, строки, boolean и неизвестные поля отклоняются с 422.
Оба запроса доступны только активному администратору со Staff JWT (роль 1).

Миграция `0098` создаёт таблицу и добавляет одну запись через `INSERT INTO screen_settings DEFAULT VALUES`.
