---
id: 0012
title: Исключить гонку отзыва токенов и удаления аккаунта против login и refresh
areas: [api, auth, db, users, tests]
date: 2026-11-23
---

# 0012. Исключить гонку отзыва токенов и удаления аккаунта против login и refresh

## Проблема
Проверка токенов (`src/db/auth.py::_resolve_token`) не проверяет, что аккаунт владельца не удалён (`User.is_deleted`), а операции отзыва сессий и изменения статуса аккаунта (`DELETE /users/me`, `PUT /users/me/password`, `POST /auth/logout-all`) не сериализуются с выпуском новых токенов (`POST /auth/login`, `POST /auth/refresh`). Из-за этого параллельный вход или обновление токена может оставить активную сессию уже после удаления аккаунта, смены пароля или выхода со всех устройств.

## Как возникает и к чему приводит

1. **Отсутствие проверки `User.is_deleted` в `_resolve_token` (`src/db/auth.py`)**
   - *Как возникает:* `_resolve_token` проверяет только наличие строки в `access_tokens`/`refresh_tokens` и `expires_at`, не связывая запрос с `users.is_deleted`.
   - *Негативный эффект:* любой токен удалённого аккаунта, переживший удаление (например, из-за гонок ниже), продолжает авторизовывать запросы. Методы `POST /articles`, `POST /articles/{id}/comments`, `PUT .../like`/`dislike` и `POST /auth/refresh` не перепроверяют `is_user_not_exist`, поэтому удалённый аккаунт может публиковать контент, ставить реакции и обновлять токены в нарушение `decisions/0005-soft-delete.md`.

2. **Гонка `POST /auth/login` против `DELETE /users/me`, `PUT /users/me/password` и `POST /auth/logout-all` (`src/backend.py::login`, `delete_user`, `change_password`)**
   - *Как возникает:* `login` читает хеш пароля и выполняет 600 000 итераций PBKDF2 (~200–500 мс — широкое окно для гонки), а затем выпускает новую пару токенов без блокировки строки пользователя. Пока идёт хеширование, параллельный `delete_user`, `change_password` или `logout-all` успевает закоммитить удаление аккаунта / смену пароля и `revoke_all_tokens`, после чего `login` коммитит свежую пару токенов.
   - *Негативный эффект:* злоумышленник со старым паролем получает валидную сессию уже после смены пароля или удаления аккаунта, а при `logout-all` в системе остаётся сессия, инициированная до отзыва.

3. **Гонка `POST /auth/refresh` против `DELETE /users/me`, `PUT /users/me/password` и `POST /auth/logout-all` (`src/backend.py::refresh_session`, `src/api/routes/auth_logout_all.py`)**
   - *Как возникает:* `refresh_session` успевает прочитать действующий `refresh_token` до коммита `revoke_all_tokens`. После того как `delete_user`, `change_password` или `logout-all` удаляет все токены и коммитит, `refresh_session` вызывает `revoke_refresh_token` (отсутствующий токен тихо игнорируется) и вставляет новую пару токенов.
   - *Негативный эффект:* отозванная сессия «воскресает» с новой парой валидных токенов уже после выхода со всех устройств, смены пароля или удаления аккаунта.

## Желаемое поведение
- `src/db/auth.py::_resolve_token` проверяет `User.is_deleted == False`: любой токен (и access, и refresh) удалённого аккаунта всегда отклоняется с `401 /errors/invalid-token`.
- Операции `delete_user`, `change_password`, `logout-all`, `login` и `refresh_session` строго сериализуются эксклюзивной блокировкой (`FOR UPDATE`) на строке пользователя в `users`:
  - после `DELETE /users/me` параллельный `login` или `refresh` не может выпустить действующие токены и получает `401`;
  - после `PUT /users/me/password` параллельный `login` со старым паролем или параллельный `refresh` со старым токеном не может выпустить действующие токены и получает `401`;
  - после `POST /auth/logout-all` параллельный `refresh` с ранее выданным токеном получает `401`, а `login`, начавшийся до `logout-all`, либо завершается раньше (и его токены отзываются), либо полностью выполняется уже после `logout-all`;
  - два параллельных `POST /auth/refresh` с одним и тем же `refresh_token` также строго сериализуются: выигрывает ровно один запрос (`200`), остальные получают `401 /errors/invalid-token`.
- Операции разных пользователей не блокируют друг друга и не приводят к deadlock и `500`.

## Готово, когда
- `auth.resolve_access_token` и `auth.resolve_refresh_token` отклоняют токены пользователя с `is_deleted = True`.
- Параллельные `login` и `refresh` против `DELETE /users/me`, `PUT /users/me/password` и `POST /auth/logout-all` не оставляют активных токенов после отзыва/удаления/смены пароля.
- Параллельные `POST /auth/refresh` с одним `refresh_token` выдают ровно один `200`, а остальные завершаются с `401`.
- Обновлены пометки о параллельном `POST /auth/refresh` в `issues/0006-account-security.md` и `decisions/0009-api-atomicity.md`.
- Добавлены детерминированные регрессионные тесты (unit и/или e2e с воспроизведением гонки), полный `make test` проходит.
