import os
import logging
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

# ================== CONFIG ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8542011335  # CHANGE THIS TO YOUR ACTUAL TELEGRAM ID

# ================== LOGGING ==================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== DATA STORAGE ==================
user_data = {}

# Profile fields and prompts
FIELDS = ["name", "age", "language", "phone", "looking_for", "bio"]
PROMPTS = {
    "name": "📝 Enter your name:",
    "age": "🎂 Enter your age:",
    "language": "🗣️ Languages you speak (comma separated):",
    "phone": "📞 Phone number (or type 'skip' to skip):",
    "looking_for": "💑 Who are you looking for?",
    "bio": "✨ Write two attractive lines about yourself:"
}

# ================== COMMAND HANDLERS ==================
def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    
    if user_id == ADMIN_ID:
        update.message.reply_text("👑 Admin Panel - Use /notify <user_id>")
        return
    
    user_data[user_id] = {"step": 0, "data": {}, "photos": []}
    update.message.reply_text(f"👋 Welcome!\n\n{PROMPTS['name']}")

def handle_text(update: Update, context: CallbackContext):
    """Handle text messages for profile creation."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if user_id not in user_data:
        update.message.reply_text("Please start with /start")
        return
    
    user_info = user_data[user_id]
    step = user_info["step"]
    
    if step >= len(FIELDS):
        return
    
    field = FIELDS[step]
    
    if field == "phone" and text.lower() == "skip":
        user_info["data"][field] = "Not shared"
    else:
        user_info["data"][field] = text
    
    user_info["step"] += 1
    
    if user_info["step"] < len(FIELDS):
        next_field = FIELDS[user_info["step"]]
        update.message.reply_text(PROMPTS[next_field])
    else:
        update.message.reply_text("✅ All info collected! Now send 1-3 photos 📸")

def handle_photo(update: Update, context: CallbackContext):
    """Handle photo messages."""
    user_id = update.effective_user.id
    
    if user_id not in user_data:
        update.message.reply_text("Please start with /start")
        return
    
    user_info = user_data[user_id]
    
    if user_info["step"] < len(FIELDS):
        field = FIELDS[user_info["step"]]
        update.message.reply_text(f"Please complete: {PROMPTS[field]}")
        return
    
    # Store photo
    photo = update.message.photo[-1]
    if "photos" not in user_info:
        user_info["photos"] = []
    user_info["photos"].append(photo.file_id)
    
    photo_count = len(user_info["photos"])
    
    if photo_count == 1:
        update.message.reply_text("📸 Photo 1 received. Send up to 2 more.")
    elif photo_count == 2:
        update.message.reply_text("📸 Photo 2 received. Send 1 more or type 'done' to finish.")
    elif photo_count >= 3:
        submit_profile(update, context, user_id, user_info)

def submit_profile(update: Update, context: CallbackContext, user_id: int, user_info: dict):
    """Submit the completed profile to admin."""
    try:
        profile_text = (
            "🌟 NEW PROFILE 🌟\n\n"
            f"👤 Name: {user_info['data'].get('name', 'N/A')}\n"
            f"🎂 Age: {user_info['data'].get('age', 'N/A')}\n"
            f"🗣️ Language: {user_info['data'].get('language', 'N/A')}\n"
            f"📞 Phone: {user_info['data'].get('phone', 'N/A')}\n"
            f"💑 Looking for: {user_info['data'].get('looking_for', 'N/A')}\n"
            f"✨ Bio: {user_info['data'].get('bio', 'N/A')}\n\n"
            f"🆔 User ID: {user_id}\n"
            f"👤 Username: @{update.effective_user.username or 'N/A'}"
        )
        
        # Send photos to admin
        for i, photo_id in enumerate(user_info.get('photos', [])[:3], 1):
            context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo_id,
                caption=profile_text if i == 1 else f"Photo {i} of {len(user_info['photos'])}"
            )
        
        # Confirm to user
        update.message.reply_text(
            "✅ Profile submitted!\n"
            "Admin will contact you if matched. ❤️\n"
            "Use /start for new profile."
        )
        
        # Clean up
        if user_id in user_data:
            del user_data[user_id]
            
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("❌ Error. Use /start to try again.")

def notify(update: Update, context: CallbackContext):
    """Admin command to notify a user about a match."""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not context.args:
        update.message.reply_text("Usage: /notify <user_id>")
        return
    
    try:
        target_id = int(context.args[0])
        context.bot.send_message(
            chat_id=target_id,
            text="❤️ Someone liked your profile! We'll connect you soon."
        )
        update.message.reply_text(f"✅ Notification sent to {target_id}")
    except:
        update.message.reply_text("❌ Invalid user ID")

def main():
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("No BOT_TOKEN found!")
        return
    
    logger.info("Starting bot...")
    
    # Create Updater - OLD STABLE SYNTAX
    updater = Updater(BOT_TOKEN, use_context=True)
    
    # Get dispatcher
    dp = updater.dispatcher
    
    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("notify", notify))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    
    # Start polling
    updater.start_polling()
    logger.info("Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
