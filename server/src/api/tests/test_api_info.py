"""
Этот файл служит для проверки синхронности маршрутов API (`src/api/routes/`) и
обработчиков `OPTIONS` в `src/api/api_info.py`, а также формата ответов `OPTIONS`.
"""

import re

# Импорт `src.api.api` регистрирует все маршруты из `src/api/routes/` на `shared.app`.
import src.api.api  # noqa: F401
from src.api import shared


def test_routes_and_options_are_in_sync() -> None:
    route_methods: dict[str, set[str]] = {}
    options_rules: set[str] = set()

    for rule in shared.app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        if rule.endpoint.startswith("info."):
            assert rule.methods == {"OPTIONS"}, rule.rule
            assert rule.rule not in options_rules, rule.rule
            options_rules.add(rule.rule)
        else:
            methods = {m.lower() for m in (rule.methods - {"HEAD", "OPTIONS"})}
            assert methods, rule.rule
            route_methods.setdefault(rule.rule, set()).update(methods)

    # Защита от ложного успеха, если маршруты не зарегистрировались.
    assert len(route_methods) > 0
    assert set(route_methods.keys()) == options_rules

    client = shared.app.test_client()
    for rule_path, expected_methods in sorted(route_methods.items()):
        url = re.sub(r"<[^>]+>", "1", rule_path)
        response = client.options(url)
        assert response.status_code == 200, rule_path
        assert response.mimetype == "application/json", rule_path
        data = response.get_json()
        assert isinstance(data, dict), rule_path
        assert set(data.keys()) == expected_methods, rule_path
