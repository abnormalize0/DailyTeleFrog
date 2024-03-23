Основные API методы
===================

Все методы API представлены в файле ``/server/src/api/api.py``.
Все API сетоды возвращают словарь, в котором содержится как минимум статус операции. Статус имеет следующую структуру:

.. code-block:: python

    {
        'type': 'OK' or 'Error'
        'error_type': 'OptionError' or 'ValueError'
        'message': '%STR%'
    }

Наличие поля ``type`` гарантируется. По значению этого поля можно определить завершился ли запрос на сервер успешно.
Если значение поля ``OK``, то запрос завершился корректно. В противном случае значение поля будет ``ERROR``.
Если запрос совершился с ошибкой, то все остальные поля кроме статуса будут содержать значение ``NONE``.
Остальные два поля являются опциональными. Оба поля присутствуют в словаре статуса только в том случае, если
запрос завершился с ошибкой. Поле ``error_type`` содержит в себе тип ошибки. Значение ``OptionError`` сигнализирует
о том, что в переданных параметрах была допущена ошибка, например было передано неверное название опции. Значение
``ValueError`` сигнализирует о том, у одно из параметров неверное значение, например для *id* пользователя имеет
значение ``0``. Поле ``message`` содержит сообщение с подробным описанием возникшей проблемы.

api_article_post()
^^^^^^^^^^^^^^^^^^

Метод для опубликования статьи.

.. code-block:: python

    @app.route('/article', methods=['POST'])
    def api_article_post()
    """
    :request:
    {
        'name': 'login',
        'type': 'str',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'article-body',
        'type': 'json',
        'is_required': True,
        'container': 'body',
        'structure': []
    },
    {
        'name': 'preview-content',
        'type': 'json',
        'is_required': True,
        'container': 'body',
        'structure': []
    },
    {
        'name': 'name',
        'type': 'str',
        'is_required': True,
        'container': 'body',
    },
    {
        'name': 'tags',
        'type': 'str',
        'is_required': True,
        'container': 'body',
    },

    :returns: str(json) in format {'status': %JSON%, 'article_id': %INT%}
    """

Ключ ``article-body`` содержит тело статьи со структурой определенной пользователем.
Сервер никак не изменяет статью, которую ему передали, и не обращается к ее содержимому.
Поэтому вся структура сохраняется в неизменном виде. Это позволяет определить структуру статьи на строрне *frontend* и
изменять ее без необходимости вносить изменения на сервер.

Ключ ``preview-content`` содержит *json* с контентом, который требуется для предпоказа в ленте.
Сервер никак не изменяет структуру и не обращается к ее содержимому.
Это позволяет определить структуру контента для предпоказа на строрне *frontend* и
изменять ее без необходимости вносить изменения на сервер.

Ключ ``name`` содержит название статьи.

Ключ ``tags`` содержит теги статьи, перечисленные через разделитель ``~``. Напирмер, статья имеющая теги ``Обзор``,
``Call of Duty`` и ``Лонг`` будет иметь значение по ключу ``tags``: ``~Обзор~Call of duty~Лонг~``.

При публикации статьи для нее автоматически заводится следующие поля:

* Поле ``creation_date``, в котором хранится дата публикации статьи в милисекундах от 1970 года

.. note::
    Сервер сохраняет только перечисленные ключи и их значения.
    Все остальные ключи будут проигнорированы, а данные по ним будут утеряны.

.. note::
    Незалогиненные пользователи не могут опубликовать статью. Если на сервер отправить запрос на публикацию статьи для
    пользователя с *id* равным 0, то сервер вернет ошибку.

api_article_get()
^^^^^^^^^^^^^^^^^

Метод для получения статьи.

.. code-block:: python

    @app.route('/article', methods=['GET'])
    def api_article_get()
    """
    :request:
    {
        'name': 'article-id',
        'type': 'int',
        'is_required': True,
        'container': 'header'
    }

    :returns: str(json) in format {'status': %JSON%, 'article': %JSON%}
    """

Этот метод обрабатывает только один заголовок - *id* статьи, которую нужно вернуть.
Метод читает все необходимые данные о статье с требуемым *id* и возвращает статью в формате *json*.
Статья имеет следующую структуру:

.. code-block:: python

    {
        'article_body': '%JSON%' # user-defined article structure
        'preview_content': '%JSON%' # user-defined preview structure
        'name': '%STR%'
        'author_preview': {
                            'nickname': '%STR%'
                            'avatar': '%STR%'
                          }
        'answers': [
                        '%COMMENT_ID%': {
                                            'comment_text': '%STR%'
                                            'author_id': '%INT%'
                                            'likes_count': '%INT%'
                                            'id': '%INT%'
                                            'answers': '%LIST%'
                        },
                        'ANOTHER_COMMENT_ID': {
                        },
                        ...
                    ]
        'likes_count': '%INT%'
        'likes_id': '%STR%'
        'comments_count': '%INT%'
        'tags': '%STR%'
        'creation_date': '%STR%'
    }

Ключ ``article_body`` содержит тело статьи со структурой определенной пользователем.
Сервер никак не изменяет статью, которую ему передали, и не обращается к ее содержимому.
Поэтому вся структура сохраняется в неизменном виде. Это позволяет определить структуру статьи на строрне *frontend* и
изменять ее без необходимости вносить изменения на сервер.

Ключ ``preview_content`` содержит *json* с контентом, который требуется для предпоказа в ленте.
Сервер никак не изменяет структуру и не обращается к ее содержимому.
Это позволяет определить структуру контента для предпоказа на строрне *frontend* и
изменять ее без необходимости вносить изменения на сервер.

Ключ ``name`` содержит название статьи.

Ключ ``author_preview`` содержит *json* с данными об авторе для предпоказа. Данные об авторе содержат *login*
пользователя, доступный по ключу ``nickname`` и ссылку на аватар автора, доступную по ключу ``avatar``.

Ключ ``answers`` содержит список коментариев и ответов к ним.
Этот список содержит древовиднусюб структуру комментариев.
В списке первого уровня лежат комментарии, которые пользователи написали к статье.
У каждого комментария есть список ответов, в котором содержаться комментарии с такой же структурой.
Для каждого комментария определены ключи ``comment_text``, который соджержит текст комментария, ``author_id``,
который содержит значение *id* автора комментария, ``likes_count``, котоырый содержит количество лайков
на комментарии, ``id``, который содержит *id* комментария и ``answers``, который содержит список ответов
на комментарий.

Ключ ``likes_count`` содержит количество лайков статьи. Ключ ``comments_count`` содержит количество комментариев статьи.

Ключ ``likes_id`` содержит *id* пользователей, который лайкнули статью, перечисленные через разделитель ``~``.
Напирмер, статья имеющая лайки от пользователей с *id* ``1`` и ``2`` будет иметь значение по ключу ``likes_id``:
``~1~~2~``.

Ключ ``tags`` содержит теги статьи, перечисленные через разделитель ``~``. Напирмер, статья имеющая теги ``Обзор``,
``Call of Duty`` и ``Лонг`` будет иметь значение по ключу ``tags``: ``~Обзор~~Call of duty~~Лонг~``.

Ключ ``creation_date`` содержит дату публикации статьи в милисекундых от 1970 года.

api_article_info_post()
^^^^^^^^^^^^^^^^^^^^^^^

Метод для обновления информации о посте.

.. code-block:: python

    @app.route('/article/data', methods=['POST'])
    """
    :request:
    {
        'name': 'login',
        'type': 'str',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'article-id',
        'type': 'int',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'like-article',
        'type': 'json',
        'is_required': False,
        'container': 'body',
        'structure': []
    },
    {
        'name': 'dislike-article',
        'type': 'json',
        'is_required': False,
        'container': 'body',
        'structure': []
    },
    {
        'name': 'like-comment',
        'type': 'json',
        'is_required': False,
        'container': 'body',
        'structure': [
            {
                'name': 'comment_id',
                'type': 'int',
                'is_required': True
            }
        ]
    },
    {
        'name': 'dislike-comment',
        'type': 'json',
        'is_required': False,
        'container': 'body',
        'structure': [
            {
                'name': 'comment_id',
                'type': 'int',
                'is_required': True
            }
        ]
    },
    {
        'name': 'add-comment',
        'type': 'json',
        'is_required': False,
        'container': 'body',
        'structure': [
            {
                'name': 'root',
                'type': 'int',
                'is_required': True
            },
            {
                'name': 'text',
                'type': 'str',
                'is_required': True
            }
        ]
    }

    :returns: str(json) in format {'status': %JSON%, 'comment_id': %INT%}
    """

Заголовок ``login`` содержит *id* пользователя, для которого запрашиваются страницы со статьями.
Если страницы запрашиваются для незалогиненного пользователя, то этот заголовок должен содержать значение ``0``.
Заголовок ``article-id`` содержит *id* статьи для которой будет выполняться команда.
В запросе к серверу должна присутсвовать одна из команд ``like-article``, ``dislike-article``, ``like-comment``,
``dislike-comment`` или ``add-comment``.

При запросе к серверу с одной из команд ``like-article``, ``dislike-article``, ``like-comment`` или
``dislike-comment`` рейтинг автора статьи или комментария изменится автоматически.

.. note::
    Незалогиненные пользователи не могут оставлять комментарии, лайкать и дизлайкать.
    Если на сервер отправить такой запрос для пользователя с *id* равным 0,
    то сервер вернет ошибку.

api_article_data_get()
^^^^^^^^^^^^^^^^^^^^^^

Метод для получения информации о посте.

.. code-block:: python

    @app.route('/article/data', methods=['GET'])
    def api_article_data_get()
    """
    :request:
    {
        'name': 'article-id',
        'type': 'int',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'requested-data',
        'type': 'list',
        'is_required': True,
        'container': 'header',
        'structure': [
            {
                'name': 'likes_count',
                'type': 'field',
                'is_required': False,
            },
            {
                'name': 'likes_id',
                'type': 'field',
                'is_required': False,
            },
            {
                'name': 'dislikes_count',
                'type': 'field',
                'is_required': False,
            },
            {
                'name': 'dislikes_id',
                'type': 'field',
                'is_required': False,
            },
            {
                'name': 'comments_count',
                'type': 'field',
                'is_required': False,
            },
            {
                'name': 'creation_date',
                'type': 'field',
                'is_required': False,
            }
        ]
    }

    :returns: str(json) in format {'status': %JSON%, %KEY1%: %ANSWER%, %KEY2%: %ANSWER%...}
    """

Заголовок ``article-id`` содержит *id* статьи для которой будет выполняться команда.
Ключ ``requested-data`` содержит строку, которая будет преобразована сервером в список запрашиваемых данных. Например,
``requested-data`` может содержать значение ``~likes_count~likes_id~dislikes_count~dislikes_id~comments_count~``.

Ответ содержит все ключи, перечисленные в запросе. По каждому ключу лежит запрашиваемое значение.

api_pages_get()
^^^^^^^^^^^^^^^

Метод позволяет получить страницы с несколькими статьями на каждой.

.. code-block:: python

    @app.route('/pages', methods=['GET'])
    def api_pages_get()
    """
    :request:
    {
        'name': 'login',
        'type': 'str',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'indexes',
        'type': 'list_of_int',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'include-nonsub',
        'type': 'bool',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'sort-column',
        'type': 'str',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'sort-direction',
        'type': 'str',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'upper-date',
        'type': 'date',
        'is_required': False,
        'container': 'header'
    },
    {
        'name': 'lower-date',
        'type': 'date',
        'is_required': False,
        'container': 'header'
    },
    {
        'name': 'upper-rating',
        'type': 'int',
        'is_required': False,
        'container': 'header'
    },
    {
        'name': 'lower-rating',
        'type': 'int',
        'is_required': False,
        'container': 'header'
    },
    {
        'name': 'include-tags',
        'type': 'list',
        'is_required': False,
        'container': 'header',
        'structure': []
    },
    {
        'name': 'exclude-tags',
        'type': 'list',
        'is_required': False,
        'container': 'header',
        'structure': []
    },
    {
        'name': 'include-authors',
        'type': 'list',
        'is_required': False,
        'container': 'header',
        'structure': []
    },
    {
        'name': 'exclude-authors',
        'type': 'list',
        'is_required': False,
        'container': 'header',
        'structure': []
    },
    {
        'name': 'include-communities',
        'type': 'list',
        'is_required': False,
        'container': 'header',
        'structure': []
    },
    {
        'name': 'exclude-communities',
        'type': 'list',
        'is_required': False,
        'container': 'header',
        'structure': []
    },

    :returns: str(json) in format {'status': %JSON%, 'pages': %JSON%}
    """

Заголовок ``login`` содержит *id* пользователя, для которого запрашиваются страницы со статьями.
Если страницы запрашиваются для незалогиненного пользователя, то этот заголовок должен содержать значение ``0``.
Заголовок ``indexes`` содержит список *id* запрашиваемых страниц перечисленных через символ ``~``.
Например, заголовок может содержать значение ``~1~2~3~``.
Ключ ``include-nonsub`` является флагом для включения в выборку постов, в которых нет информации, на которую
пользователь подписан.
Ключ ``sort-column`` содержит в себе значение, по которому должны быть отсортированы посты в выдаче.
Значение обязано быть одним из ``creation_date`` или ``rating``.
Ключ ``sort-direction`` содержит в себе значение направлюения сортировки.
Для сортировки по убыванию значение должно быть ``descending``.
Для сортировки по возрастанию значение должно быть ``ascending``.
Ключи ``upper-date``, ``lower-date``, ``upper-rating`` и ``lower-rating`` содержат в себе границы для соответствующих
параметров статей.
Ключи ``include-tags``, ``include-authors`` и ``include-communities`` содержат в себе параметры, все из которых должны
присутствовать в статьях в выборке.
Ключи ``exclude-tags``, ``exclude-authors`` и ``exclude-communities`` содержат в себе параметры, ни один из которых
не должен присутствовать в статьях в выборке.


Возвращаемый ``JSON`` содержит ключ *pages*, который содержит запрашиваемые страницы со следующей структурой:

.. code-block:: python

    'REQUIRED_INDEX': [
        {
            'id': '%INT%'
            'preview_content': '%JSON%' # user-defined preview structure
            'name': '%STR%'
            'author_preview': {
                                'nickname': '%STR%'
                                'avatar': '%STR%'
                            }
            'likes_count': '%INT%'
            'likes_id': '%LIST_OF_INT%'
            'dislikes_count': '%INT%'
            'dislikes_id': '%LIST_OF_INT%'
            'comments_count': '%INT%'
            'tags': '%STR%'
            'creation_date': '%STR%'
        },
        {
            'ANOTHER ARTICLE'
        },
        ...
    ],
    'ANOTHER_REQUIRED_INDEX': [
        {
            'ARTICLE'
        },
        {
            'ARTICLE'
        }
        ...
    ]

Ключ ``pages`` содержит список ключей, которые совпадаю с запрашиваемыми индексами страниц.
Значение по каждому ключу содержит список с контентом для предпоказа статьи.
Во возвращаемых страницах содержаться только незаблокированные у пользователя статьи.

Контент для предпоказа статьи содерждит следующие ключи:

Ключ ``id`` содержит *id* статьи

Ключ ``preview_content`` содержит *json* с контентом, который требуется для предпоказа в ленте.
Сервер никак не изменяет структуру и не обращается к ее содержимому.
Это позволяет определить структуру контента для предпоказа на строрне *frontend* и
изменять ее без необходимости вносить изменения на сервер.

Ключ ``name`` содержит название статьи.

Ключ ``author_preview`` содержит *json* с данными об авторе для предпоказа. Данные об авторе содержат *login*
пользователя, доступный по ключу ``nickname`` и ссылку на аватар автора, доступную по ключу ``avatar``.

Ключ ``likes_count`` содержит количество лайков статьи.
Ключ ``likes_id`` содержит id пользователей, которые поставили лайк статье.
Ключ ``dislikes_count`` содержит количество дизлайков статьи.
Ключ ``dislikes_id`` содержит id пользователей, которые поставили дизлайк статье.
Ключ ``comments_count`` содержит количество комментариев статьи.

Ключ ``tags`` содержит теги статьи, перечисленные через разделитель ``~``. Напирмер, статья имеющая теги ``Обзор``,
``Call of Duty`` и ``Лонг`` будет иметьlikes_id значение по ключу ``tags``: ``~Обзор~Call of duty~Лонг~``.

Ключ ``creation_date`` содержит дату публикации статьи в милисекундах от 1970 года.

.. note::
    Для незалогиненных пользователей метод работает, считая, что для такого пользователя нет заблокированных тегов.

.. note::
    Индексы страниц начинаются с ``0``.

api_users_post()
^^^^^^^^^^^^^^^^

Метод для регистрации нового пользователя.

.. code-block:: python

    @app.route('/users', methods=['POST'])
    def api_users_post()
    """
    :request:
    {
        'name': 'name',
        'type': 'str',
        'is_required': True,
        'container': 'body',
    },
    {
        'name': 'email',
        'type': 'str',
        'is_required': True,
        'container': 'body',
    },
    {
        'name': 'password',
        'type': 'str',
        'is_required': True,
        'container': 'body',
    },
    {
        'name': 'avatar',
        'type': 'str',
        'is_required': False,
        'container': 'body',
    },
    {
        'name': 'sub-tags',
        'type': 'list',
        'is_required': False,
        'container': 'body',
        'structure': [],
    },
    {
        'name': 'blocked-tags',
        'type': 'list',
        'is_required': False,
        'container': 'body',
        'structure': [],
    },
    {
        'name': 'sub-authors',
        'type': 'list',
        'is_required': False,
        'container': 'body',
        'structure': [],
    },
    {
        'name': 'blocked-authors',
        'type': 'list',
        'is_required': False,
        'container': 'body',
        'structure': [],
    },
    {
        'name': 'sub-communities',
        'type': 'list',
        'is_required': False,
        'container': 'body',
        'structure': [],
    },
    {
        'name': 'blocked-communities',
        'type': 'list',
        'is_required': False,
        'container': 'body',
        'structure': [],
    },
    {
        'name': 'description',
        'type': 'str',
        'is_required': False,
        'container': 'body',
    }

    :returns: str(json) in format {'status': %JSON%, 'user_id': %INT%}
    """

Метод возвращает *id* созданного пользователя.
Поле ``avatar`` является ссылкой на аватарку пользователя.
Поле ``sub-tags`` является списком тегов, на которые пользователь подписан, разделенных символом ``~``.
Например, это поле может иметь значение ``~Рикролл~MMO~nsfw~``.
Поле ``blocked-tags`` является списком заблокированных тегов, разделенных символом ``~``.
Поле ``sub-authors`` является списком авторов, на которые пользователь подписан, разделенных символом ``~``.
Поле ``blocked-authors`` является списком заблокированных авторов, разделенных символом ``~``.
Поле ``sub-communities`` является списком сообществ, на которые пользователь подписан, разделенных символом ``~``.
Поле ``blocked-communities`` является списком заблокированных сообществ, разделенных символом ``~``.
Поле ``description`` содержит в себе текстовое описарние профиля.

При регистрации пользователя для него автоматически заводится следующие поля:

* Поле ``name_history``, в котором хранится история имен пользователя
* Поле ``creation_date``, в котором хранится дата регистрации пользователя в милисекундах от 1970 года
* Поле ``rating``, в котором текуший рейтинг пользователя

api_users_data_post()
^^^^^^^^^^^^^^^^^^^^^

Метод, изменяющий пользовательские данные.

.. code-block:: python

    @app.route('/users/data', methods=['POST'])
    def api_users_data_post()
    """
    :request:
    {
        'name': 'login',
        'type': 'str',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'nickname',
        'type': 'str',
        'is_required': False,
        'container': 'body',
    },
    {
        'name': 'email',
        'type': 'str',
        'is_required': False,
        'container': 'body',
    },
    {
        'name': 'avatar',
        'type': 'str',
        'is_required': False,
        'container': 'body',
    },
    {
        'name': 'sub-tags',
        'type': 'list',
        'is_required': False,
        'container': 'body',
        'structure': [],
    },
    {
        'name': 'blocked-tags',
        'type': 'list',
        'is_required': False,
        'container': 'body',
        'structure': [],
    },
    {
        'name': 'sub-authors',
        'type': 'list',
        'is_required': False,
        'container': 'body',
        'structure': [],
    },
    {
        'name': 'blocked-authors',
        'type': 'list',
        'is_required': False,
        'container': 'body',
        'structure': [],
    },
    {
        'name': 'sub-communities',
        'type': 'list',
        'is_required': False,
        'container': 'body',
        'structure': [],
    },
    {
        'name': 'blocked-communities',
        'type': 'list',
        'is_required': False,
        'container': 'body',
        'structure': [],
    },
    {
        'name': 'description',
        'type': 'str',
        'is_required': False,
        'container': 'body',
    }

    :returns: str(json) in format {'status': %JSON%}
    """

Метод принимает только один заголовок с *id* пользователя.
Поле ``nickname`` соответствует никнейму пользователя.
Поле ``email`` соответствует почте пользователя.
Поле ``avatar`` является ссылкой на аватарку пользователя.
Поле ``sub-tags`` является списком тегов, на которые пользователь подписан, разделенных символом ``~``.
Например, это поле может иметь значение ``~Рикролл~MMO~nsfw~``.
Поле ``blocked-tags`` является списком заблокированных тегов, разделенных символом ``~``.
Поле ``sub-authors`` является списком авторов, на которые пользователь подписан, разделенных символом ``~``.
Поле ``blocked-authors`` является списком заблокированных авторов, разделенных символом ``~``.
Поле ``sub-communities`` является списком сообществ, на которые пользователь подписан, разделенных символом ``~``.
Поле ``blocked-communities`` является списком заблокированных сообществ, разделенных символом ``~``.
Поле ``description`` содержит в себе текстовое описарние профиля.

Если было обновлено поле ``nickname``, то поле ``name_history`` будет обновлено сервером автоматически.

.. note::
    Если поле ``login`` будет содержать значение 0, то сервер вернет ошибку.
    Нельзя обновить данные о незалогиненном пользователе.

api_users_data_get()
^^^^^^^^^^^^^^^^^^^^

Метод, позволяющий получить всю информацию о пользователе, необходимую для отображения страницы профиля.

.. code-block:: python

    @app.route('/users/data', methods=['GET'])
    def api_users_data_get()
    """
    :request:
    {
        'name': 'login',
        'type': 'str',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'requested-data',
        'type': 'list',
        'is_required': True,
        'container': 'header',
        'structure': [
            {
                'name': 'nickname',
                'type': 'field',
                'is_required': False,
            },
            {
                'name': 'email',
                'type': 'str',
                'is_required': False,
            },
            {
                'name': 'name_history',
                'type': 'field',
                'is_required': False,
            },
            {
                'name': 'avatar',
                'type': 'field',
                'is_required': False,
            },
            {
                'name': 'sub_tags',
                'type': 'field',
                'is_required': False,
                'container': 'body',
            },
            {
                'name': 'blocked_tags',
                'type': 'field',
                'is_required': False,
                'container': 'body',
            },
            {
                'name': 'sub_authors',
                'type': 'field',
                'is_required': False,
                'container': 'body',
            },
            {
                'name': 'blocked_authors',
                'type': 'field',
                'is_required': False,
                'container': 'body',
            },
            {
                'name': 'sub_communities',
                'type': 'field',
                'is_required': False,
                'container': 'body',
            },
            {
                'name': 'blocked_communities',
                'type': 'field',
                'is_required': False,
                'container': 'body',
            },
            {
                'name': 'description',
                'type': 'field',
                'is_required': False,
            },
            {
                'name': 'creation_date',
                'type': 'field',
                'is_required': False,
            },
            {
                'name': 'rating',
                'type': 'field',
                'is_required': False,
            }
        ]
    }

    :returns: str(json) in format {'status': %JSON%, %KEY1%: %ANSWER%, %KEY2%: %ANSWER%...}
    """

Заголовок ``login`` содержит *id* пользователя, для которого запрашивается информация о профиле.
Ключ ``requested-data`` содержит строку, которая будет преобразована сервером в список запрашиваемых данных. Например,
``requested-data`` может содержать значение ``~nickname~email~name_history~avatar~blocked_tags~description~creation_date~``.

Ответ содержит все ключи, перечисленные в запросе. По каждому ключу лежит запрашиваемое значение.

.. note::
    Если поле ``login`` будет содержать значение 0, то сервер вернет ошибку.
    Нельзя получить информацию о незалогиненном пользователе.

api_users_password_post()
^^^^^^^^^^^^^^^^^^^^^^^^^

Метод смены пользовательского пароля.

.. code-block:: python

    @app.route('/users/password', methods=['POST'])
    def api_users_password_post()
    """
    :request:
    {
        'name': 'login',
        'type': 'str',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'previous-password',
        'type': 'str',
        'is_required': True,
        'container': 'header'
    },
    {
        'name': 'new-password',
        'type': 'str',
        'is_required': True,
        'container': 'body'
    }

    :returns: str(json) in format {'status': %JSON%}
    """

Заголовок ``login`` содержит *id* пользователя, который хочет сменить пароль. Заголовок ``previous-password``
содержит старый пароль пользователя. Если старый пароль будет указан неверно, то пароль не будет обновлен.
Поле ``new-password`` содержит новый пароль, который пользователь хочет установить.

.. note::
    Если поле ``login`` будет содержать значение 0, то сервер вернет ошибку.
    Нельзя обновить пароль для незалогиненного пользователя.

api_login_get()
^^^^^^^^^^^^^^^

Метод для проверки пользовательского пароля.

.. code-block:: python

    @app.route('/login', methods=['GET'])
    def api_login_get()
    """
    :request:
    {
        'name': 'login',
        'type': 'str',
        'is_required': False,
        'container': 'header',
    },
    {
        'name': 'email',
        'type': 'str',
        'is_required': False,
        'container': 'header',
    },
    {
        'name': 'password',
        'type': 'str',
        'is_required': True,
        'container': 'header',
    }

    :returns: str(json) in format {'status': %JSON%, 'is-correct': %BOOL%}
    """

Заголовок ``login`` содержит *id* пользователя, для которого происходит проверка пароля.
Заголовок ``email`` содержит *email* пользователя, для которого происходит проверка пароля.
Заголовок ``password`` содержит пароль, которой нужно проверить.
При отсутсвии пользователя с *id* ``is-correct`` будет содержать значение ``False``

.. note::
    Если поле ``login`` будет содержать значение 0, то сервер вернет ошибку.
    Нельзя проверить пароль у незалогиненного пользователя.