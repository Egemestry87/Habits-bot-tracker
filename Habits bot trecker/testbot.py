import telebot

# Put your actual token here
BOT_TOKEN = "8303069304:AAHlM7sf8zkus-qjyDR2nPL_-qsozynnR4A"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ Bot is working! Hello!")

if __name__ == '__main__':
    if BOT_TOKEN == "YOUR_ACTUAL_BOT_TOKEN_HERE":
        print("❌ Please replace with your actual bot token")
    else:
        print("🤖 Testing bot...")
        try:
            bot.infinity_polling()
        except Exception as e:
            print(f"Error: {e}")
