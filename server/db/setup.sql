USE db;

CREATE TABLE users (
    username VARCHAR(32) NOT NULL,
    email VARCHAR(32) NOT NULL,
    nickname VARCHAR(32) NOT NULL,
    password VARCHAR(23) NOT NULL,
    creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    avatar VARCHAR(32),
    description TEXT,
    PRIMARY KEY (username, email),
    UNIQUE (email)
);

CREATE TABLE user_name_history (
    username VARCHAR(32) NOT NULL,
    old_name VARCHAR(512) NOT NULL,
    PRIMARY KEY (username, old_name),
    FOREIGN KEY (username) REFERENCES users(username)
);

CREATE TABLE tag_subscriptions (
    tag_name VARCHAR(512) NOT NULL,
    username VARCHAR(32) NOT NULL,
    PRIMARY KEY (tag_name, username),
    FOREIGN KEY (username) REFERENCES users(username)
);

CREATE TABLE tag_blacklist (
    tag_name VARCHAR(512) NOT NULL,
    username VARCHAR(32) NOT NULL,
    PRIMARY KEY (tag_name, username),
    FOREIGN KEY (username) REFERENCES users(username)
);

CREATE TABLE user_subscriptions (
    username VARCHAR(32) NOT NULL,
    subscribed_user VARCHAR(32) NOT NULL,
    PRIMARY KEY (username, subscribed_user),
    FOREIGN KEY (username) REFERENCES users(username),
    FOREIGN KEY (subscribed_user) REFERENCES users(username)
);

CREATE TABLE user_blacklist (
    username VARCHAR(32) NOT NULL,
    blocked_user VARCHAR(32) NOT NULL,
    PRIMARY KEY (username, blocked_user),
    FOREIGN KEY (username) REFERENCES users(username),
    FOREIGN KEY (blocked_user) REFERENCES users(username)
);

CREATE TABLE articles (
    id BIGINT AUTO_INCREMENT NOT NULL,
    title VARCHAR(512) NOT NULL,
    creation_date BIGINT NOT NULL,
    body VARCHAR(512) NOT NULL,
    author_username VARCHAR(32) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (author_username) REFERENCES users(username)
);

CREATE TABLE article_tags (
    tag_name VARCHAR(512) NOT NULL,
    article_id BIGINT NOT NULL,
    PRIMARY KEY (tag_name, article_id),
    FOREIGN KEY (article_id) REFERENCES articles(id)
);

CREATE TABLE article_preview (
    article_id BIGINT NOT NULL,
    preview_content VARCHAR(512) NOT NULL,
    PRIMARY KEY (article_id),
    FOREIGN KEY (article_id) REFERENCES articles(id)
);

CREATE TABLE article_likes (
    article_id BIGINT NOT NULL,
    author_username VARCHAR(32) NOT NULL,
    PRIMARY KEY (article_id, author_username),
    FOREIGN KEY (article_id) REFERENCES articles(id),
    FOREIGN KEY (author_username) REFERENCES users(username)
);

CREATE TABLE article_dislikes (
    article_id BIGINT NOT NULL,
    author_username VARCHAR(32) NOT NULL,
    PRIMARY KEY (article_id, author_username),
    FOREIGN KEY (article_id) REFERENCES articles(id),
    FOREIGN KEY (author_username) REFERENCES users(username)
);

CREATE TABLE comments (
    id BIGINT AUTO_INCREMENT NOT NULL,
    article_id BIGINT NOT NULL,
    author_username VARCHAR(32) NOT NULL,
    text VARCHAR(512) NOT NULL,
    creation_date BIGINT NOT NULL,
    root_id BIGINT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (article_id) REFERENCES articles(id),
    FOREIGN KEY (author_username) REFERENCES users(username)
);

CREATE TABLE comment_likes (
    comment_id BIGINT NOT NULL,
    author_username VARCHAR(32) NOT NULL,
    PRIMARY KEY (comment_id, author_username),
    FOREIGN KEY (comment_id) REFERENCES comments(id),
    FOREIGN KEY (author_username) REFERENCES users(username)
);

CREATE TABLE comment_dislikes (
    comment_id BIGINT NOT NULL,
    author_username VARCHAR(32) NOT NULL,
    PRIMARY KEY (comment_id, author_username),
    FOREIGN KEY (comment_id) REFERENCES comments(id),
    FOREIGN KEY (author_username) REFERENCES users(username)
);