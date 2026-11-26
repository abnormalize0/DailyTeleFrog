---
id: 0032
title: Унифицировать проверку существования в src/db на одиночный SELECT
areas: [db, users, articles, comments, tests]
date: 2026-11-23
---

# 0032. Унифицировать проверку существования в src/db на одиночный SELECT

## Проблема
В `src/db/` сосуществуют два конкурирующих паттерна проверки существования записи: часть функций делает один `SELECT` с `is_deleted == False` и проверяет `row is None` (`user.preview`, `article.delete`, `comment.delete`), а большинство остальных сначала вызывает `is_*_not_exist` и сразу следом делает второй почти идентичный `SELECT` той же строки.

## Как возникает и к чему приводит
- *Как возникает:* в `src/db/user.py` (`delete`, `check_password`, `change_password`, `update_email`, `update_nickname`, `update_description`, `update_avatar`, `_get_user_field`), `src/db/article.py` (`get`, `like`, `dislike`) и `src/db/comment.py` (`like`, `dislike`, `creation_date`) проверка существования вынесена в отдельный `if is_*_not_exist(...): return not_found(...)`, после чего выполняется второй `SELECT` по тому же ключу.
- *Негативный эффект:*
  - каждая такая операция делает 2 `SELECT` вместо 1;
  - под `READ COMMITTED` между двумя `SELECT` возникает TOCTOU-окно (например, в `check_password`: если между `is_user_not_exist` и выборкой `User.password` сменится `email` или аккаунт будет мягко удалён, второй запрос вернёт `None` или не проверит `is_deleted`);
  - в кодовой базе закреплены два разных стиля для одной и той же задачи, что путает при добавлении новых функций в `src/db/` (дополняет оптимизацию составных чтений из `issues/0022-avoid-full-row-fetches.md`).

## Желаемое поведение
- Функции в `src/db/user.py`, `src/db/article.py` и `src/db/comment.py`, которым и так нужна строка или колонка сущности, читают её за один `SELECT` с фильтром `is_deleted == False` и возвращают `not_found`, если результат `None` (по единому образцу с `user.preview`, `article.delete`, `comment.delete`).
- `is_*_not_exist` остаётся только там, где сама строка родителя не нужна, а операция идёт с другой (дочерней/связующей) таблицей (например, `backend.add_comment` проверяет наличие статьи перед вставкой комментария, `article.remove_like` проверяет наличие статьи перед `DELETE` лайка).
- В докстрингах/комментариях функций `is_*_not_exist` явно зафиксировано это правило (когда использовать `is_*_not_exist`, а когда делать одиночный `SELECT ... WHERE is_deleted == False`), чтобы при добавлении новых функций не возвращаться к двойному запросу.
- Внешнее поведение всех функций и коды ошибок (`NotFound`, `Forbidden` и т.д.) не меняются.

## Готово, когда
- Функции чтения и обновления одиночной сущности в `src/db/user.py`, `src/db/article.py` и `src/db/comment.py` не делают двойного `SELECT` одной и той же строки.
- В докстрингах/комментариях `is_*_not_exist` описана граница применения между одиночным `SELECT` и `is_*_not_exist`.
- Все существующие unit- и e2e-тесты проходят, полный `make test` зелёный.
