---
id: 0035
title: Переименовать таблицу article_preview в article_previews
areas: [db, articles, tests]
date: 2026-11-23
---

# 0035. Переименовать таблицу article_preview в article_previews

## Проблема
Таблица `article_preview` в `src/db/scheme/article_preview.py` названа в единственном числе, тогда как все остальные таблицы исчисляемых сущностей в схеме БД названы во множественном числе (`articles`, `users`, `comments`, `article_likes` и т.д.).

## Как возникает и к чему приводит
- *Как возникает:* при создании `ArticlePreview` в `src/db/scheme/article_preview.py` было задано `__tablename__ = "article_preview"` вместо множественного числа.
- *Негативный эффект:*
  - нарушение единого соглашения об именовании таблиц исчисляемых сущностей (в отличие от собирательных/неисчисляемых `user_blacklist`, `tag_blacklist`, `user_name_history`, которые естественно остаются в единственном числе).

## Желаемое поведение
- Переименовать `__tablename__` в `src/db/scheme/article_preview.py` с `"article_preview"` на `"article_previews"` (пока в БД нет боевых данных и миграций, внешние ключи и тесты на имя `"article_preview"` не завязаны).
- Обновить упоминания имени таблицы `article_preview` в докстрингах и комментариях (`src/db/scheme/article_preview.py`, `src/api/routes/articles.py`).
- Собирательные/неисчисляемые таблицы `user_blacklist`, `tag_blacklist`, `user_name_history` не переименовывать (исключение фиксируется в `.agents/skills/dailytelefrog-db-schema/SKILL.md` в рамках `issues/0034-sync-docs-decisions-and-skills.md`).

## Готово, когда
- В `src/db/scheme/article_preview.py` указано `__tablename__ = "article_previews"`, докстринги и комментарии обновлены.
- Полный `make test` проходит.
