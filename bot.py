import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8542011335  # CHANGE THIS

# Storage
user_data = {}

def start(update, context):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        update.message.reply_text("👑 Admin online")
        return
    
    user_data[user_id] = {"step": "name"}
    update.message.reply_text("👋 Welcome! Enter your name:")

def handle_text(update, context):
    user_id = update.effective_user.id
    
    if user_id not in user_data:
        update.message.reply_text("Type /start first")
        return
    
    step = user_data[user_id]["step"]
    text = update.message.text
    
    if step == "name":
        user_data[user_id]["name"] = text
        user_data[user_id]["step"] = "age"
        update.message.reply_text("🎂 Enter your age:")
    elif step == "age":
        user_data[user_id]["age"] = text
        user_data[user_id]["step"] = "done"
        update.message.reply_text("✅ Profile saved! Admin will review it.")

def notify(update, context):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    
    if context.args:
        try:
            target_id = int(context.args[0])
            context.bot.send_message(target_id, "❤️ Someone liked your profile!")
            update.message.reply_text("Notification sent")
        except:
            update.message.reply_text("Invalid ID")

def main():
    if not BOT_TOKEN:
        logger.error("No BOT_TOKEN!")
        return
    
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("notify", notify))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    
    updater.start_polling()
    logger.info("✅ Bot is running!")
    updater.idle()

if __name__ == '__main__':
    main()
