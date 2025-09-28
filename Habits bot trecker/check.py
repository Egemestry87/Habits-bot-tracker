try:
    import telebot
    print("✅ telebot imported successfully")
    print("✅ Version:", telebot.__version__)
except ImportError as e:
    print("❌ telebot import failed:", e)

# Check token
BOT_TOKEN = "8303069304:AAHlM7sf8zkus-qjyDR2nPL_-qsozynnR4A"
if BOT_TOKEN.startswith("YOUR") or len(BOT_TOKEN) < 40:
    print("❌ Token not set correctly")
else:
    print("✅ Token format looks good")
    print("Token length:", len(BOT_TOKEN))
