# DailyTeleFrog

Сборка документации клиента
---

Для сборки документации клиента необходимо установить `Sphinx` и `Sphinx RTD Theme`:

```
pip install Sphinx
pip install sphinx-rtd-theme
```

После этого документацию можно собрать. Для этого перейдите в директорию `/client/doc` и выполните команду:

```
make html
```

Теперь документацию можно открыть. Для этого перейдите в директорию `/client/doc/build/html` и откройте файл `index.html`.
