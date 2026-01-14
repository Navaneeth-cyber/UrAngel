import os
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


def start(update: Update, context: CallbackContext):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        update.message.reply_text("✅ Admin online.")
        return

    temp[uid] = {}
    update.message.reply_text(PROMPTS["name"])


def collect_text(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    if uid not in temp:
        return

    data = temp[uid]
    text = update.message.text.strip()

    for field in FIELDS:
        if field not in data:
            if field == "phone" and text.lower() == "skip":
                data[field] = "Not shared"
            else:
                data[field] = text

            next_field = next((f for f in FIELDS if f not in data), None)

            if next_field:
                update.message.reply_text(PROMPTS[next_field])
            else:
                update.message.reply_text("✅ All information collected! Now send your photos (1-3).")
            return


def collect_photo(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    if uid not in temp:
        update.message.reply_text("Please start with /start first.")
        return

    data = temp[uid]

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

    # Forward photo + send details
    update.message.forward(chat_id=ADMIN_ID)
    context.bot.send_message(chat_id=ADMIN_ID, text=caption)

    update.message.reply_text(
        "✅ Done!\n"
        "If someone liked your profile, we'll inform you ❤️\n"
        "Admin will contact you if matched."
    )

    # 🔥 DELETE USER DATA IMMEDIATELY
    if uid in temp:
        del temp[uid]


def notify(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        update.message.reply_text("Usage: /notify <user_id>")
        return

    try:
        target_id = int(context.args[0])
        context.bot.send_message(
            chat_id=target_id,
            text="❤️ Someone liked your profile!\nWe'll connect you soon."
        )
        update.message.reply_text(f"✅ Notification sent to user {target_id}")
    except:
        update.message.reply_text("Invalid user ID.")


def main():
    print("Starting bot...")
    
    # Create the Updater
    updater = Updater(token=BOT_TOKEN, use_context=True)
    
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("notify", notify))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, collect_text))
    dp.add_handler(MessageHandler(Filters.photo, collect_photo))

    # Start polling
    print("Bot started. Polling...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
