import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import datetime
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ⚠️ REPLACE THIS WITH YOUR ACTUAL BOT TOKEN FROM BOTFATHER ⚠️
BOT_TOKEN = "8303069304:AAHlM7sf8zkus-qjyDR2nPL_-qsozynnR4A"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('habits_bot.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER,
                date TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0
            )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id, username, first_name):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO users (user_id, username, first_name) VALUES (?, ?, ?)', 
                      (user_id, username, first_name))
        self.conn.commit()
    
    def add_habit(self, user_id, habit_name):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO habits (user_id, name) VALUES (?, ?)', (user_id, habit_name))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_user_habits(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name FROM habits WHERE user_id = ?', (user_id,))
        return cursor.fetchall()
    
    def mark_habit_completion(self, habit_id, date):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO completions (habit_id, date, completed) VALUES (?, ?, 1)', 
                      (habit_id, date))
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

# Initialize database
db = Database()

# Command handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    db.add_user(user.id, user.username, user.first_name)
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📋 My Habits", callback_data='my_habits'))
    keyboard.add(InlineKeyboardButton("➕ Add Habit", callback_data='add_habit'))
    keyboard.add(InlineKeyboardButton("✅ Today's Progress", callback_data='today'))
    
    bot.reply_to(message, 
        f"👋 Hello {user.first_name}!\n\n"
        "🏋️ Welcome to Habits Tracker Bot!\n\n"
        "Track your daily habits and build better routines.",
        reply_markup=keyboard
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
🤖 **Habits Tracker Bot Commands:**

/start - Start the bot
/help - Show this help message
/today - Show today's progress
/habits - List your habits
/add - Add a new habit

**How to use:**
1. Add habits using 'Add Habit'
2. Mark them as completed daily
3. Track your progress over time
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['today'])
def show_today(message):
    user_id = message.from_user.id
    show_today_progress(user_id, message.chat.id)

@bot.message_handler(commands=['habits'])
def show_habits(message):
    user_id = message.from_user.id
    show_my_habits(user_id, message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == 'my_habits':
        show_my_habits(user_id, chat_id, message_id)
    elif call.data == 'add_habit':
        prompt_add_habit(chat_id, message_id)
    elif call.data == 'today':
        show_today_progress(user_id, chat_id, message_id)
    elif call.data.startswith('mark_habit_'):
        habit_id = int(call.data.split('_')[-1])
        mark_habit_done(user_id, habit_id, chat_id, message_id)
    elif call.data == 'main_menu':
        show_main_menu(chat_id, message_id)

def show_my_habits(user_id, chat_id, message_id=None):
    habits = db.get_user_habits(user_id)
    
    if not habits:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("➕ Add Habit", callback_data='add_habit'))
        
        if message_id:
            bot.edit_message_text(
                "You haven't added any habits yet. Use 'Add Habit' to get started!",
                chat_id, message_id, reply_markup=keyboard
            )
        else:
            bot.send_message(chat_id, 
                "You haven't added any habits yet. Use 'Add Habit' to get started!",
                reply_markup=keyboard
            )
        return
    
    text = "📋 **Your Habits:**\n\n"
    keyboard = InlineKeyboardMarkup()
    
    for habit_id, habit_name in habits:
        text += f"• {habit_name}\n"
        keyboard.add(InlineKeyboardButton(f"✅ Mark {habit_name}", callback_data=f'mark_habit_{habit_id}'))
    
    keyboard.add(InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu'))
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=keyboard)
    else:
        bot.send_message(chat_id, text, reply_markup=keyboard)

def show_today_progress(user_id, chat_id, message_id=None):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    completions = db.get_today_completions(user_id)
    
    text = f"📅 **Today's Progress** ({datetime.datetime.now().strftime('%B %d, %Y')})\n\n"
    keyboard = InlineKeyboardMarkup()
    
    completed_count = 0
    for habit_id, habit_name, completed in completions:
        status = "✅" if completed else "⏳"
        text += f"{status} {habit_name}\n"
        
        if not completed:
            keyboard.add(InlineKeyboardButton(f"Mark '{habit_name}' as Done", callback_data=f'mark_habit_{habit_id}'))
        else:
            completed_count += 1
    
    if completed_count == len(completions) and completions:
        text += "\n🎉 **All habits completed for today! Great job!**"
    
    keyboard.add(InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu'))
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=keyboard)
    else:
        bot.send_message(chat_id, text, reply_markup=keyboard)

def mark_habit_done(user_id, habit_id, chat_id, message_id):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    db.mark_habit_completion(habit_id, today)
    
    habits = db.get_user_habits(user_id)
    habit_name = next((name for hid, name in habits if hid == habit_id), "Unknown Habit")
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📅 Back to Today", callback_data='today'))
    keyboard.add(InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu'))
    
    bot.edit_message_text(
        f"✅ **Great job!**\n\n'{habit_name}' marked as completed for today! 🎉",
        chat_id, message_id, reply_markup=keyboard
    )

def prompt_add_habit(chat_id, message_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Cancel", callback_data='main_menu'))
    
    bot.edit_message_text(
        "📝 **Add a New Habit**\n\n"
        "Please send me the name of your new habit:\n\n"
        "Examples:\n"
        "• Morning exercise\n"
        "• Read 30 minutes\n"
        "• Drink water\n"
        "• Meditation",
        chat_id, message_id, reply_markup=keyboard
    )

def show_main_menu(chat_id, message_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📋 My Habits", callback_data='my_habits'))
    keyboard.add(InlineKeyboardButton("➕ Add Habit", callback_data='add_habit'))
    keyboard.add(InlineKeyboardButton("✅ Today's Progress", callback_data='today'))
    
    bot.edit_message_text(
        "🏠 **Main Menu**\n\nChoose an option:",
        chat_id, message_id, reply_markup=keyboard
    )

# Handle text messages for adding habits
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Check if we're in "add habit" mode (simple implementation)
    user_id = message.from_user.id
    habit_name = message.text
    
    # Simple check: if message doesn't start with /, consider it a habit name
    if not message.text.startswith('/'):
        habit_id = db.add_habit(user_id, habit_name)
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("✅ Today's Progress", callback_data='today'))
        keyboard.add(InlineKeyboardButton("📋 My Habits", callback_data='my_habits'))
        
        bot.reply_to(message,
            f"✅ **Habit added successfully!**\n\n"
            f"'{habit_name}' has been added to your habits list.",
            reply_markup=keyboard
        )
    else:
        bot.reply_to(message, "Use the buttons or commands to interact with the bot!")

# Start the bot
if __name__ == '__main__':
    if BOT_TOKEN == "YOUR_ACTUAL_BOT_TOKEN_HERE":
        print("❌ ERROR: Please replace BOT_TOKEN with your actual bot token!")
        print("Get it from @BotFather on Telegram")
    else:
        print("🤖 Bot starting...")
        try:
            bot.infinity_polling()
        except Exception as e:
            print(f"❌ Error: {e}")
