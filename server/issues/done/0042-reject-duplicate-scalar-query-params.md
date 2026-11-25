---
id: 0042
title: Отклонять дублирующиеся скалярные query-параметры в read_query
areas: [api, tests]
date: 2026-11-25
---

# 0042. Отклонять дублирующиеся скалярные query-параметры в read_query

## Проблема
`src/api/shared.py::read_query` для скалярных query-параметров (`str`, `int`, `bool`) читает только первое значение через `request.args[name]` и молча отбрасывает все повторные значения того же параметра.

## Как возникает и к чему приводит
- *Как возникает:* при обработке `element["type"] != "list"` в `shared.read_query` вызывается `_parse_query_value(request.args[name], element["type"])` (в отличие от списочных параметров, для которых используется `request.args.getlist(name)`).
- *Негативный эффект:*
  - запрос вида `?indexes=0&sort_column=rating&sort_column=creation_date` или `?indexes=0&upper_date=100&upper_date=bogus` молча игнорирует второй параметр и выполняется так, будто его не было, вместо явной ошибки валидации;
  - повторные значения скалярного параметра не проходят через `check_structure` (в том числе если во втором значении переданы некорректные данные или `\x00` как `?sort_column=rating&sort_column=a%00b`).

## Желаемое поведение
- Если скалярный query-параметр (элемент схемы с `type != "list"`) передан в query-строке более одного раза (`len(request.args.getlist(name)) > 1`), `read_query` отклоняет его с `422 /errors/validation`, добавляя в `errors` элемент с `pointer: "/<name>"` и понятным `detail`.
- Повторяющиеся списочные параметры (`type == "list"`, например `?indexes=0&indexes=1` или `?requested_data=nickname&requested_data=email`) продолжают работать как раньше.

## Готово, когда
- `shared.read_query` отклоняет дублирующиеся скалярные query-параметры с `422 /errors/validation` и `pointer: "/<name>"`.
- Списочные query-параметры по-прежнему принимают несколько значений.
- Добавлены регрессионные unit- и e2e-тесты, полный `make test` проходит.
