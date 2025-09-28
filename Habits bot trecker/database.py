import sqlite3
import datetime
from config import DATABASE_FILE

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Habits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Completions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER,
                date TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                notes TEXT,
                rating INTEGER,
                photo_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits (id)
            )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id, username, first_name):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name) 
            VALUES (?, ?, ?)
        ''', (user_id, username, first_name))
        self.conn.commit()
    
    def add_habit(self, user_id, habit_name):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO habits (user_id, name) VALUES (?, ?)
        ''', (user_id, habit_name))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_user_habits(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name FROM habits WHERE user_id = ?', (user_id,))
        return cursor.fetchall()
    
    def mark_habit_completion(self, habit_id, date, notes="", rating=0, photo_url=""):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO completions 
            (habit_id, date, completed, notes, rating, photo_url) 
            VALUES (?, ?, 1, ?, ?, ?)
        ''', (habit_id, date, notes, rating, photo_url))
        self.conn.commit()
    
    def get_today_completions(self, user_id):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT h.id, h.name, c.completed 
            FROM habits h 
            LEFT JOIN completions c ON h.id = c.habit_id AND c.date = ?
            WHERE h.user_id = ?
        ''', (today, user_id))
        return cursor.fetchall()
    
    def delete_habit(self, habit_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM habits WHERE id = ?', (habit_id,))
        cursor.execute('DELETE FROM completions WHERE habit_id = ?', (habit_id,))
        self.conn.commit()

# Create global database instance
db = Database()
