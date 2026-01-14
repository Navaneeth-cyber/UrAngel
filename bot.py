import os
import logging
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    Application
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8542011335  # CHANGE THIS TO YOUR TELEGRAM ID

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
async def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    logger.info(f"User {user_id} ({username}) started the bot")
    
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "👑 Admin Panel\n\n"
            "Commands:\n"
            "/notify <user_id> - Send match notification\n"
            "/stats - Show bot statistics"
        )
        return
    
    # Initialize user data
    user_data[user_id] = {
        "step": 0,
        "data": {},
        "photos": []
    }
    
    await update.message.reply_text(
        f"👋 Welcome {username}!\n\n"
        "I'll help you create a dating profile.\n\n"
        "Let's start with some basic information.\n\n"
        f"{PROMPTS['name']}"
    )


async def handle_text(update: Update, context: CallbackContext):
    """Handle text messages for profile creation."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Skip if user hasn't started
    if user_id not in user_data:
        await update.message.reply_text("Please start with /start")
        return
    
    user_info = user_data[user_id]
    current_step = user_info["step"]
    
    # Admin commands for admin only
    if user_id == ADMIN_ID and text.startswith("/"):
        return
    
    # If we're collecting photos info
    if current_step >= len(FIELDS):
        return
    
    current_field = FIELDS[current_step]
    
    # Handle phone field skip
    if current_field == "phone" and text.lower() in ["skip", "skipp"]:
        user_info["data"][current_field] = "Not shared"
    else:
        user_info["data"][current_field] = text
    
    user_info["step"] += 1
    
    # Check if all fields are filled
    if user_info["step"] < len(FIELDS):
        next_field = FIELDS[user_info["step"]]
        await update.message.reply_text(PROMPTS[next_field])
    else:
        await update.message.reply_text(
            "✅ Great! All information collected!\n\n"
            "Now please send 1-3 photos 📸\n"
            "(Send them one by one)"
        )


async def handle_photo(update: Update, context: CallbackContext):
    """Handle photo messages."""
    user_id = update.effective_user.id
    
    # Skip if user hasn't started
    if user_id not in user_data:
        await update.message.reply_text("Please start with /start")
        return
    
    user_info = user_data[user_id]
    
    # Check if all fields are filled
    if user_info["step"] < len(FIELDS):
        current_field = FIELDS[user_info["step"]]
        await update.message.reply_text(f"Please complete: {PROMPTS[current_field]}")
        return
    
    # Store photo
    photo = update.message.photo[-1]  # Get highest resolution
    user_info["photos"].append(photo.file_id)
    
    photo_count = len(user_info["photos"])
    
    if photo_count == 1:
        await update.message.reply_text("📸 Photo received! You can send up to 2 more photos.")
    elif photo_count == 2:
        await update.message.reply_text("📸 Second photo received! You can send one more.")
    elif photo_count >= 3:
        # Submit profile
        await submit_profile(update, context, user_id, user_info)


async def submit_profile(update: Update, context: CallbackContext, user_id: int, user_info: dict):
    """Submit the completed profile to admin."""
    try:
        # Create profile summary
        profile_text = (
            "🌟 NEW PROFILE SUBMISSION 🌟\n\n"
            f"👤 Name: {user_info['data']['name']}\n"
            f"🎂 Age: {user_info['data']['age']}\n"
            f"🗣️ Language: {user_info['data']['language']}\n"
            f"📞 Phone: {user_info['data']['phone']}\n"
            f"💑 Looking for: {user_info['data']['looking_for']}\n"
            f"✨ Bio: {user_info['data']['bio']}\n\n"
            f"🆔 User ID: {user_id}\n"
            f"👤 Username: @{update.effective_user.username or 'N/A'}\n"
            f"📸 Photos: {len(user_info['photos'])}"
        )
        
        # Send photos to admin
        for i, photo_id in enumerate(user_info['photos'], 1):
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo_id,
                caption=profile_text if i == 1 else f"Photo {i} of {len(user_info['photos'])}"
            )
        
        # Send text summary to admin (in case photos fail)
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=profile_text
        )
        
        # Confirm to user
        await update.message.reply_text(
            "✅ Profile submitted successfully!\n\n"
            "Your profile is now with our admin.\n"
            "If someone likes your profile, we'll notify you! ❤️\n\n"
            "Use /start to create another profile."
        )
        
        # Clean up
        if user_id in user_data:
            del user_data[user_id]
            
    except Exception as e:
        logger.error(f"Error submitting profile: {e}")
        await update.message.reply_text(
            "❌ Error submitting profile. Please try again with /start"
        )


async def notify(update: Update, context: CallbackContext):
    """Admin command to notify a user about a match."""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ This command is for admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /notify <user_id>")
        return
    
    try:
        target_id = int(context.args[0])
        message = " ".join(context.args[1:]) if len(context.args) > 1 else "❤️ Someone liked your profile! We'll connect you soon."
        
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🎉 MATCH ALERT!\n\n{message}"
        )
        
        await update.message.reply_text(f"✅ Notification sent to user {target_id}")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be a number.")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def stats(update: Update, context: CallbackContext):
    """Admin command to show bot statistics."""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        return
    
    stats_text = (
        f"🤖 Bot Statistics\n\n"
        f"📊 Active users creating profiles: {len(user_data)}\n"
        f"👥 Total fields collected: {sum(len(data['data']) for data in user_data.values())}\n"
    )
    
    await update.message.reply_text(stats_text)


async def cancel(update: Update, context: CallbackContext):
    """Cancel the current operation."""
    user_id = update.effective_user.id
    
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text("❌ Operation cancelled. Use /start to begin again.")


async def error_handler(update: Update, context: CallbackContext):
    """Log errors."""
    logger.warning(f"Update {update} caused error {context.error}")


# ================== MAIN FUNCTION ==================
def main():
    """Start the bot."""
    # Check for token
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables!")
        return
    
    logger.info("Starting bot...")
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("notify", notify))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Register message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    logger.info("Bot is running and polling...")
    application.run_polling()


if __name__ == '__main__':
    main()
