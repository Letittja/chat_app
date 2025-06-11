import sqlite3

class Database:
    def __init__(self, db_path="chat.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_user_table()
        self.create_message_table()
        self.create_group_tables()

    def create_user_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash BLOB NOT NULL
            )
        """)
        self.conn.commit()

    def user_exists(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username=?", (username,))
        return cursor.fetchone() is not None

    def create_user(self, username, password_hash):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        self.conn.commit()

    def get_user_password_hash(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM users")
        return [row[0] for row in cursor.fetchall()]

    def create_message_table(self):
        """Cria a tabela para armazenar mensagens offline."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offline_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def save_message(self, sender, receiver, message):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO offline_messages (sender, receiver, message) VALUES (?, ?, ?)",
            (sender, receiver, message)
        )
        self.conn.commit()
        
    def get_and_delete_messages_for(self, receiver):
        cursor = self.conn.cursor()
        cursor.execute("SELECT sender, message FROM offline_messages WHERE receiver=?", (receiver,))
        messages = cursor.fetchall()
        if messages:
            cursor.execute("DELETE FROM offline_messages WHERE receiver=?", (receiver,))
            self.conn.commit()
        return messages


    def create_group_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                name TEXT PRIMARY KEY
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                group_name TEXT,
                username TEXT,
                FOREIGN KEY (group_name) REFERENCES groups(name) ON DELETE CASCADE,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
                PRIMARY KEY (group_name, username)
            )
        """)
        self.conn.commit()

    def group_exists(self, group_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM groups WHERE name=?", (group_name,))
        return cursor.fetchone() is not None

    def create_group(self, group_name):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
        self.conn.commit()

    def add_group_member(self, group_name, username):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO group_members (group_name, username) VALUES (?, ?)", (group_name, username))
        self.conn.commit()

    def get_group_members(self, group_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM group_members WHERE group_name=?", (group_name,))
        return [row[0] for row in cursor.fetchall()]

    def get_all_groups(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM groups")
        return [row[0] for row in cursor.fetchall()]