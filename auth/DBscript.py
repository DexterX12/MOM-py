import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "UserDB")

# try:
#     os.makedirs("MOM-py/server/database", exist_ok=True)

#     connection = sqlite3.connect("MOM-py/server/database/UserDB")
#     cursor = connection.cursor()
#     # cursor.execute("CREATE TABLE Users (Id INTEGER PRIMARY KEY AUTOINCREMENT, UserName TEXT UNIQUE NOT NULL, Password TEXT NOT NULL)")
#     # cursor.execute("INSERT INTO Users (UserName, Password) VALUES (?, ?)", ("admin", "admin"))
#     # connection.commit
#     cursor.execute("SELECT * FROM Users")
#     user = cursor.fetchone()
#     print(user)
#     connection.close()

# except Exception as ex:
#     print(ex)
    
def auth(User, pw):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Users WHERE UserName = ? AND Password = ?", (User, pw))
        user = cursor.fetchone()

        if user:
            return {
                "id": user[0],
                "username": user[1]
            }
        else:
            return None

def get_user(id):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Users WHERE Id = ?", (id,))
        id = cursor.fetchone()
        return {
                "id": id[0],
                "username": id[1]
            }



   

