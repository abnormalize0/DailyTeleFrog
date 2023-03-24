import os
CURRENTDIRECTORY = os.getcwd()
DELIMITER = '~'
BACKUPDIRECTORY = os.path.join(CURRENTDIRECTORY, "backup")
USERSDIRECTORY = os.path.join(CURRENTDIRECTORY, "users")
USERSDB = os.path.join(USERSDIRECTORY, "users.db")
ARTICLEDIRECTORY = os.path.join(CURRENTDIRECTORY, "articles")
ARTICLESDB = os.path.join(ARTICLEDIRECTORY, "articles.db")