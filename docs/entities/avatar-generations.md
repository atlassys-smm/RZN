# Задания генерации аватаров

Задания хранятся в PostgreSQL и переживают перезапуск API. Пользователь определяется
по QR-привязке терминала. Допускается несколько активных генераций; максимальный
срок задания — 24 часа с момента создания. Истечение этого срока не удаляет файлы.

## AvatarGeneration — `avatar_generations`

| Поле | Тип | Назначение |
|------|-----|------------|
| `id` | bigint, PK | Внутренний ID |
| `request_id` | string(36), unique | UUID Kernel, неизменный при повторах FaceAI |
| `job_id` | string(128), unique, nullable | ID FaceAI, появляется после ответа или webhook |
| `user_id` | FK users | Владелец задания |
| `device_id` | FK devices, nullable | Терминал создания; при удалении устройства SET NULL |
| `profession_id` | FK professions | Профессия результата |
| `template_id` | bigint | ID комплекта на момент создания; снимок без FK |
| `gender` | int | 1 — мужской, 2 — женский образ |
| `avatar_identity` | string(64) | `<template_id>_male` или `<template_id>_female` |
| `selfie_file_id` | FK files | Сохранённое селфи |
| `reference_file_id` | FK files | Исходный файл выбранного образа шаблона, не превью и без копирования |
| `status` | int | 1 pending, 2 queued, 3 processing, 4 done, 5 failed, 6 expired |
| `user_avatar_id` | FK user_avatars, unique, nullable | Созданная фотография; при удалении SET NULL |
| `error_code` | string(128), nullable | Код FaceAI либо локальная причина завершения |
| `attempt_count` | int | Число попыток фоновой обработки |
| `next_attempt_at` | timestamptz | Ближайшая отправка или проверка FaceAI |
| `lease_until` | timestamptz, nullable | Временное закрепление задания за обработчиком |
| `deadline_at` | timestamptz | Создание + 24 часа |
| `completed_at` | timestamptz, nullable | Завершение, ошибка или истечение срока |
| `created_at` | timestamptz | Создание задания |
| `updated_at` | timestamptz | Последнее изменение задания |

Каждый POST создаёт отдельное задание с новым `request_id`, в том числе при
одинаковых параметрах и нескольких активных заданиях пользователя.
Задание хранит ссылку на исходный файл шаблона без создания отдельной копии.

## Повторная доставка результата

Kernel находит `avatar_generations` по `request_id` и блокирует запись на время
проверки и сохранения. Для уже завершённого задания возвращается `200` без
изменения результата, независимо от `event_id`. Задание, файл и `UserAvatar`
фиксируются общей транзакцией. Это защищает от одновременных webhook и гонки
с резервным скачиванием. `event_id` проверяется на совпадение с заголовком,
но отдельно не сохраняется.

Маршруты, настройки и взаимодействие сервисов описаны в
[подсистеме аватаров](../subsystems/profession-avatars/index.md).
