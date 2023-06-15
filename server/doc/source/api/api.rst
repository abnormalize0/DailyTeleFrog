Основные API методы
===================

Все основные методы API представлены в файле ``/server/src/api.py``. Рассмотрим все основные методы:


api_get_article()
^^^^^^^^^^^^^^^^^

Метод для получения статьи.

.. code-block:: python

    @app.route('/article', methods=['GET'])
    def api_get_article()
    """
    :headers: 'article-id' - str(int)

    :returns: article in json format
    """

.. note::

    Индексы статей начинаются с ``1``.

Этот метод обрабатывает только один заголовок - *id* статьи, которую нужно вернуть.
Метод читает все необходимые данные о статье с требуемым *id* и возвращает статью в формате *json*.

api_get_article_likes_comments()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Метод для получения количества лайков и количества комментариев у статьи.

.. code-block:: python

    @app.route('/article/likes_comments', methods=['GET'])
    def api_get_article_likes_comments()
    """
    :headers: 'article-id' - str(int)

    :returns: str(json) in format {'likes_count': %INT%, 'comments_count': %INT%}
    """

Этот метод обрабатывает только один заголовок - *id* статьи,
для которой нужно узнать количество комментариев и лайков.
Метод возвращает *json* в виде ``{'likes_count': %INT%, 'comments_count': %INT%}``,
где вместо ``%INT%`` будут находиться актуальные значения.

api_post_article()
^^^^^^^^^^^^^^^^^^

Метод для опубликования статьи.

.. code-block:: python

    @app.route('/article', methods=['POST'])
    def api_post_article()
    """
    :headers: 'article' - str(json)
              'user-id' - str(int)

    :returns: str(json) in format {'article-id': %INT%}
    """

Заголовок ``article`` является *json* объектом в строковом формате,
который представляет собой статью. Заголовок ``user-id`` содержит *id* пользователя, который публикует статью.
Метод возвращает *json* объект с *id* созданной статьи
в формате ``{'article-id': %INT%}``, где ``%INT%`` значение *id*
статьи.

api_like_article()
^^^^^^^^^^^^^^^^^^

Метод для переключения состояния лайка на статье.

.. code-block:: python

    @app.route('/article/like', methods=['POST'])
    def api_like_article()
    """
    :headers: 'user-id' - str(int)
              'article-id' - str(int)
    
    :returns: empty json
    """

Заголовок ``user-id`` содержит *id* пользователя, который нажал кнопку лайка.
Заголовок ``article-id`` содержит *id* статьи, для которой пользователь нажал кнопку лайка.
Если на этой статье уже лайк от этого пользователя, то его лайк снимется.
Если на статье нет лайка от этого пользователя, то лайк будет поставлен. Метод возращает пустой *json* объект.

api_add_comment()
^^^^^^^^^^^^^^^^^

Метод для добавления комметария к статье.

.. code-block:: python

    @app.route('/article/comments/add', methods=['POST'])
    def api_add_comment()
    '''
    :headers: 'user-id' - str(int)
              'article-id' - str(int)
              'root' - str(int)
              'text' - str

    :returns: str(json) in format {'comment-id': %INT%}
    '''

Заголовок ``user-id`` содержит *id* пользователя, которой написл комментарий. Заголовок ``article-id`` содержит *id*
статьи, к которой пишется комментарий. Заголовок ``root`` содержит *id* комментария, на который отвечает пользователь.
Если пользователь пишет комментрий к самой статье, то в заголовок ``root`` должно содержать значение ``-1``.
Заголовок ``text`` содержит в себе текст комментария. Метод возвращает *json* объект в формате
``{'comment-id': %INT%}``, где ``%INT%`` значение *id* созданного комментария.

api_like_comment()
^^^^^^^^^^^^^^^^^^

Метод для переключения состояния лайка на комментарии.

.. code-block:: python

    @app.route('/article/comments/like', methods=['POST'])
    def api_like_comment()
    """
    :headers: 'user-id' - str(int)
              'comment-id' - str(int)
    
    :returns: empty json
    """

Заголовок ``user-id`` содержит *id* пользователя, который нажал кнопку лайка.
Заголовок ``comment-id`` содержит *id* комментария, для которой пользователь нажал кнопку лайка.
Если на этом комментарии уже лайк от этого пользователя, то его лайк снимется. Если на комментарии
нет лайка от этого пользователя, то лайк будет поставлен. Метод возращает пустой *json* объект.

api_get_comments_likes()
^^^^^^^^^^^^^^^^^^^^^^^^

Метод для получения количества лайков на комментарии.

.. code-block:: python

    @app.route('/article/comments/like', methods=['GET'])
    def api_get_comments_likes():
    """
    :headers: 'comment-id' - str(int)

    :returns: str(json) in format {'likes-count': %INT%}
    """

Этот метод обрабатывает только один заголовок - *id* комментария,
для которой нужно узнать количество лайков.
Метод возвращает *json* в виде ``{'likes_count': %INT%}``,
где вместо ``%INT%`` будет находиться актуальное значения.

api_get_pages()
^^^^^^^^^^^^^^^

Метод позволяет получить страницу с несколькими статьями.

.. code-block:: python

    @app.route('/pages', methods=['GET'])
    def api_get_pages()
    """
    :headers: 'user-id' - str(int)
              'indexes' - str(list)

    :returns: str(json) in format {'likes-count': %INT%}
    """

Заголовок ``user-id`` содержит *id* пользователя, для которого запрашиваются страницы со статьями.
Если страницы запрашиваются для незалогиненного пользователя, то этот заголовок должен содержать значение ``-1``.
Заголовок ``indexes`` содержит список *id* запрашиваемых страниц перечисленных через запятую.
Например, заголовок может содержать значение ``[1,2,3]``.

.. note::
    Индексы страниц начинаются с ``1``.

api_add_user()
^^^^^^^^^^^^^^

Метод для регистрации нового пользователя.

.. code-block:: python

    @app.route('/users/new', methods=['POST'])
    def api_add_user()
    """
    :headers: 'user-info' - str(json) in format {'name': %STR%,
                                                 'password': %STR%,
                                                 'page': %STR%,
                                                 'avatar': %STR%,
                                                 'blocked_tags': %STR%}

    :returns: str(json) in format {'user-id': %INT%}
    """

Метод принимает только один заголовок с данными пользователя. Поля ``name`` и ``password`` заголовка являются
обязательными. Остальные поля опциональны. Метод возвращает *id* созданного пользователя.
Поля ``page`` и ``avatar`` являются ссылками на страницу пользователя и на его аватарку соответственно.
Поле ``blocked_tags`` является списком заблокированных тегов, разделенных запятыми.
Например, это поле может иметь значение ``shooter,mmo,nsfw``.

api_update_user_info()
^^^^^^^^^^^^^^^^^^^^^^

Метод, изменяющий пользовательские данные.

.. code-block:: python

    @app.route('/users/update', methods=['POST'])
    def api_update_user_info()
    """
    :headers: 'user-info' - str(json) in format {'page': %STR%,
                                                 'avatar': %STR%,
                                                 'blocked_tags': %STR%}

    :returns: empty json
    """

Метод принимает только один заголовок с данными пользователя. Все поля заголовка являются опциональными.
Поля ``page`` и ``avatar`` являются ссылками на страницу пользователя и на его аватарку соответственно.
Поле ``blocked_tags`` является списком заблокированных тегов, разделенных запятыми.
Например, это поле может иметь значение ``shooter,mmo,nsfw``.

api_change_user_password()
^^^^^^^^^^^^^^^^^^^^^^^^^^

Метод смены пользовательского пароля.

.. code-block:: python

    @app.route('/users/change_password', methods=['POST'])
    def api_change_user_password()
    """
    :headers: 'user-id' - str(int)
              'previous-password' - str
              'new-password' - str

    :returns: empty json
    """

Заголовок ``user-id`` содержи *id* пользователя, который хочет сменить пароль. Заголовок ``previous-password``
содержит старый пароль пользователя. Если старый пароль будет указан неверно, то пароль не будет обновлен.
Заголовок ``new-password`` содержит новый пароль, который пользователь хочет установить.

api_check_user_password()
^^^^^^^^^^^^^^^^^^^^^^^^^

Метод для проверки пользовательского пароля.

.. code-block:: python

    @app.route('/users/check_password', methods=['GET'])
    def api_check_user_password()
    """
    :headers: 'user-id' - str(int)
              'password' - str

    :returns: str(json) in format {'status': %BOOL%}
    """

Заголовок ``user-id`` содержит *id* пользователя, для которого происходит проверка пароля.
Заголовок ``password`` содержит пароль, которой нужно проверить. Метод возвращает *json* в формате
``{'status': %BOOL%}``, где вместо ``%BOOL%`` будет результат проверки.