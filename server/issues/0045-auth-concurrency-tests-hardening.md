---
id: 0045
title: Укрепить тесты конкурентности авторизации и покрыть unit-тестом require_auth(lock_user=True)
areas: [api, auth, tests]
date: 2026-11-27
---

# 0045. Укрепить тесты конкурентности авторизации и покрыть unit-тестом require_auth(lock_user=True)

## Проблема
По итогам задачи [0012](done/0012-auth-revocation-race.md) остались два пробела в тестовом покрытии:
1. В `src/api/tests/test_shared.py` нет unit-теста для `require_auth(session, lock_user=True)`, проверяющего повторный резолв токена под блокировкой `rows.lock_user` при конкурентном отзыве токена в `READ COMMITTED`. Сейчас этот сценарий проверяется только в e2e (`tests/routes/test_concurrency.py::test_logout_all_blocks_delete_user`).
2. Ряд новых e2e-тестов гонок в `tests/routes/test_concurrency.py` (`test_auth_refresh_vs_revocation`, `test_auth_login_vs_revocation`, `test_revocation_blocks_auth_refresh`, `test_revocation_blocks_auth_login`, `test_auth_login_by_email_vs_change_email`, `test_logout_all_blocks_delete_user`, `test_delete_user_vs_sub_user_no_deadlock_and_no_stale_sub`) используют `time.sleep(0.1–0.35)` для задания порядка входа потоков в транзакцию.

## Как возникает и к чему приводит
- *Как возникает:* при высокой нагрузке на CPU/БД первый поток может не успеть дойти до SQL-блокировки за фиксированные `0.1–0.35` секунды, и второй поток захватит блокировку первым.
- *Негативный эффект:* порядок выполнения потоков инвертируется. В частности, в `test_auth_login_vs_revocation[logout_all]` при старте `logout_all` раньше `login` запрос входа легитимно завершится с `200` и создаст токены уже после отзыва, что приведёт к ложному падению `assert rows["access_tokens"] == []` (флаки под нагрузкой). Отсутствие unit-теста на `require_auth(lock_user=True)` также снижает скорость локализации регрессий в `shared.py`.

## Желаемое поведение
- В `src/api/tests/test_shared.py` есть unit-тест, проверяющий `require_auth(session, lock_user=True)` (в том числе отказ с `401` при конкурентном отзыве токена/удалении аккаунта до снятия блокировки).
- E2e-тесты гонок в `tests/routes/test_concurrency.py` не зависят от `time.sleep` для порядка старта: ожидание входа первого потока в критическую секцию выполняется детерминированно (например, через опрос `performance_schema.data_locks` / `information_schema.processlist` или синхронизацию через триггер/блокировку MySQL).

## Готово, когда
- Добавлены unit-тесты на `require_auth(session, lock_user=True)` в `src/api/tests/test_shared.py`.
- Тесты гонок авторизации в `tests/routes/test_concurrency.py` переведены с `time.sleep` на детерминированную синхронизацию порядка потоков.
- Полный `make test` проходит стабильно.
