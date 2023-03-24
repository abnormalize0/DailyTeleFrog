import json
import db

def get_page_articles(index, blocked_tags):
    ARTICLES_PER_PAGE = 5
    articles = db.get_unblocked_artiles(blocked_tags)
    page_articles = []
    if len(articles) < (index + 1) * ARTICLES_PER_PAGE:
        page_articles = articles[index * ARTICLES_PER_PAGE:]
    else:
        page_articles = articles[index * ARTICLES_PER_PAGE : (index + 1) * ARTICLES_PER_PAGE]
    return page_articles

def select_preview(article):
    preview = {}
    preview["name"] = article["name"]
    preview["preview_content"] = article["preview_content"]
    preview["tags"] = article["tags"]
    preview["date"] = article["date"]
    preview["author"] = article["author"]
    return preview

def get_page(index, blocked_tags = None):
    page_articles = get_page_articles(index, blocked_tags)
    previews = []
    for article_id in page_articles:
        with open("articles/{0}.json".format(article_id)) as file:
            article = json.load(file)
            preview = select_preview(article)
            preview["id"] = article_id
            previews.append(preview)
    return previews

def get_pages(indexes, user_id):
    pages = {}
    blocked_tags = db.get_user_blocked_tags(user_id)
    for index in indexes:
        page = get_page(index, blocked_tags)
        pages[index] = page
    return pages

def get_article(id):
    article = None
    with open("articles/{0}.json".format(id)) as file:
        article = json.load(file)
    return article

def create_article_file(article_id, article):
    with open('articles/{0}.json'.format(article_id), 'w+', encoding='utf-8') as file:
        json.dump(article, file, ensure_ascii=False, indent=4)

def post_article(article, user_id):
    author_preview = db.get_author_preview(user_id)
    article["author"] = author_preview
    article_preview = select_preview(article)
    article_id = db.create_db_entry(article_preview)
    create_article_file(article_id, article)

def add_user(user_info):
    return db.add_user(user_info)

def get_likes_comments_count(article_id):
    return db.get_likes_comments_count(article_id)


if __name__ == "__main__":

    article = {
        "name": "Почему DOOM Ethernal лучшая игра",
        "preview_content": {
            "type": "image",
            "value": "link to image",
            "text": "Some text to show"
        },
        "tags": [
            "tag1",
            "tag2",
            "tag3"
        ],
        "date": {
            "year": 2023,
            "month": "февраль",
            "day": 23,
            "hour": 20,
            "min": 53,
            "sec": 40
        },
        "likes_count": 0,
        "comments": 0,
    }

    post_article(article, 1)

    print(get_article(1))

    print(get_likes_comments_count(1))

    print(get_pages([0], 1))

    user_info = {}
    user_info["name"] = "test"
    user_info["password"] = "123"
    user_info["page"] = "asd"
    user_info["avatar"] = "ref"
    user_info["blocked_tags"] = "ref"

    print(add_user(user_info))