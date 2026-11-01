"""
Этот файл служит для хранения статической проверки правила атомарности: транзакцией
управляет только API-метод, и на запрос приходится одна транзакция. Код не запускается,
поэтому правило проверяется и для метода, у которого ещё нет своего e2e-теста на
атомарность (см. decisions/0009-api-atomicity.md).
"""

import ast
from pathlib import Path

SRC_DIR = Path(__file__).parents[2]
ROUTES_DIR = SRC_DIR / "api" / "routes"


def _called_names(tree: ast.AST) -> list[str]:
    """Собирает имена всех функций и методов, вызванных внутри узла дерева.

    Args:
        tree: узел дерева.

    Returns:
        Список имён с повторами: `session.commit()` даёт "commit", `get_session()`
        даёт "get_session".
    """
    calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
    names = [call.attr for call in calls if isinstance(call, ast.Attribute)]
    return names + [call.id for call in calls if isinstance(call, ast.Name)]


def test_only_routes_finish_transaction() -> None:
    # commit внутри backend или db закрепил бы первую часть метода, и откат в конце
    # запроса уже не смог бы её отменить. rollback посреди метода опасен иначе: всё,
    # что идёт после него, попало бы в новую транзакцию отдельно от отменённой части.
    for path in SRC_DIR.rglob("*.py"):
        is_test = "tests" in path.parts or path.name == "conftest.py"
        if is_test or ROUTES_DIR in path.parents:
            continue
        names = _called_names(ast.parse(path.read_text(encoding="utf8")))
        assert "commit" not in names, path
        assert "rollback" not in names, path


def test_route_uses_one_transaction() -> None:
    # Каждая сессия и каждый commit открывают свою транзакцию, а между двумя
    # транзакциями сбой оставил бы применённой только первую половину запроса.
    methods = 0
    for path in ROUTES_DIR.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf8"))):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("api_"):
                methods += 1
                names = _called_names(node)
                assert names.count("get_session") <= 1, node.name
                assert names.count("commit") <= 1, node.name
    # Защита от ложного успеха, если файлы переедут и цикл не найдёт ни одного метода.
    assert methods > 0
