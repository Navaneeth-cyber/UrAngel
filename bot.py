from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import os

# ================== CONFIG ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# 🔒 PERMANENT ADMIN (PUT YOUR TELEGRAM NUMERIC ID HERE)
ADMIN_ID = 8542011335   # <-- CHANGE THIS ONLY

# ============================================

temp = {}

FIELDS = [
    "name",
    "age",
    "language",
    "phone",
    "looking_for",
    "bio"
]

PROMPTS = {
    "name": "Enter your name:",
    "age": "Enter your age:",
    "language": "Languages you speak:",
    "phone": "Phone number (or type Skip):",
    "looking_for": "Who are you looking for?",
    "bio": "Write two attractive lines about you:"
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        await update.message.reply_text("✅ Admin online.")
        return

    temp[uid] = {}
    await update.message.reply_text(PROMPTS["name"])


async def collect_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in temp:
        return

    data = temp[uid]
    text = update.message.text.strip()

    # Find current field to fill
    for field in FIELDS:
        if field not in data:
            if field == "phone" and text.lower() == "skip":
                data[field] = "Not shared"
            else:
                data[field] = text

            # Find next field to ask
            for next_field in FIELDS:
                if next_field not in data:
                    await update.message.reply_text(PROMPTS[next_field])
                    return
            
            # If all fields are filled
            await update.message.reply_text("✅ All info collected! Now send your photos (1–3).")
            return


async def collect_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in temp:
        await update.message.reply_text("Please start with /start first.")
        return

    data = temp.get(uid, {})

    # Check if all fields are filled
    missing_fields = [field for field in FIELDS if field not in data]
    if missing_fields:
        await update.message.reply_text(f"Please complete all fields first. Missing: {missing_fields[0]}")
        return

    caption = (
        "📩 New Profile\n\n"
        f"Name: {data['name']}\n"
        f"Age: {data['age']}\n"
        f"Language: {data['language']}\n"
        f"Phone: {data['phone']}\n"
        f"Looking for: {data['looking_for']}\n"
        f"Bio: {data['bio']}\n\n"
        f"User ID: {uid}"
    )

    try:
        # Forward photo to admin
        await update.message.forward(chat_id=ADMIN_ID)
        await context.bot.send_message(chat_id=ADMIN_ID, text=caption)
        
        await update.message.reply_text(
            "✅ Profile submitted successfully!\n"
            "If someone liked your profile, we'll inform you ❤️\n"
            "Admin will contact you if matched."
        )
    except Exception as e:
        print(f"Error sending to admin: {e}")
        await update.message.reply_text("❌ Error submitting profile. Please try again later.")
    finally:
        # Clean up user data
        if uid in temp:
            del temp[uid]


async def notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /notify <user_id>")
        return

    try:
        target_id = int(context.args[0])
        await context.bot.send_message(
            chat_id=target_id,
            text="❤️ Someone liked your profile!\nWe'll connect you soon."
        )
        await update.message.reply_text(f"✅ Notification sent to user {target_id}")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be a number.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cleanup_temp(context: ContextTypes.DEFAULT_TYPE):
    """Optional: Clean up old temporary data periodically"""
    # Remove entries older than 1 hour
    pass


def main():
    print("Starting bot...")
    
    # Create application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("notify", notify))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_text))
    app.add_handler(MessageHandler(filters.PHOTO, collect_photo))

    # Start polling
    print("Bot is polling...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
