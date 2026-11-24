"""
Этот файл служит для хранения конфигурации сервера: путей к логам, размера страницы
ленты и времени жизни токенов авторизации.
"""

import os


class DynamicPath:
    """Путь относительно текущей рабочей директории, вычисляемый при обращении к `path`."""

    def __init__(self, *args: str) -> None:
        """Сохраняет сегменты пути для дальнейшей сборки в path.

        Args:
            *args: сегменты пути.

        Returns:
            None
        """
        self.parts = args

    @property
    def path(self) -> str:
        """Собирает абсолютный путь из текущей директории и сегментов.

        Args:
            None

        Returns:
            Абсолютный путь (str).
        """
        return os.path.join(os.getcwd(), *self.parts)


log_directory = DynamicPath("log")
log_server_api = DynamicPath("log", "server_api.log")

articles_per_page = 5

# Время жизни токенов авторизации, мс (см. db/auth.py). access — короткий,
# летает в каждом запросе; refresh — длинный, но с ротацией при каждом
# использовании (см. AccessToken/RefreshToken в db/scheme/).
access_token_lifetime_ms = 60 * 60 * 1000  # 1 час
refresh_token_lifetime_ms = 30 * 24 * 60 * 60 * 1000  # 30 дней
