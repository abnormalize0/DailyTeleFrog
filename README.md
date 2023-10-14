# DailyTeleFrog

Сборка документации
---

Для сборки документации сервера необходимо установить `Sphinx` и `Sphinx RTD Theme`:

```
pip install Sphinx
pip install sphinx-rtd-theme
```

После этого документацию можно собрать. Для этого перейдите в директорию `/server/doc` для сервера или `/client/doc` для клиента и выполните команду:

```
make html
```

Теперь документацию можно открыть. Для этого перейдите в директорию `/server/doc/build/html` для сервера или `/client/doc/build/html` для клиента и откройте файл `index.html`.
