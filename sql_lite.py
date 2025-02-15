import sqlite3

# создаем подключение к БД и таблицу
def init_db():
    conn = sqlite3.connect('bot_db.db')
    cursor = conn.cursor()

    # создаем таблицу пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # создаем таблицу действий пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            requestType TEXT,
            request TEXT,
            response TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# добавление пользователя в таблицу users 
def add_user(user_id: int, username: str, first_name: str, last_name: str) -> bool: 
    conn = sqlite3.connect('bot_db.db')
    cursor = conn.cursor()

    try:
        # проверяем, существует ли пользователь
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()

        if existing_user is None:
            # добавляем пользователя, если его нет в базе данных
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
            return True
        return False
    
    except sqlite3.Error as e:
        print(f"Ошибка при работе с БД: {e}")
        return False
    finally:
        conn.close()

# добавление записи запрос и ответ
def add_new_action(user_id: int, 
                   username: str, 
                   first_name: str, 
                   last_name: str,
                   requestType: str,
                   request: str,
                   response: str) -> bool:
    conn = sqlite3.connect('bot_db.db')
    cursor = conn.cursor()

    try: 
        # сначала убедимся, что пользователь существует, если нет - создавать его
        existing_user_id = add_user(user_id, username, first_name, last_name)

        if existing_user_id is not None:
            # записываем действие пользователя
            cursor.execute('''
                INSERT INTO actions (user_id, requestType, request, response, datetime)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (existing_user_id, requestType, request, response))
            conn.commit()
            return True
        return False
    
    except sqlite3.Error as e:
        print(f"Ошибка при работе с БД: {e}")
        return False
    finally:
        conn.close()