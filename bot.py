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

    for field in FIELDS:
        if field not in data:
            if field == "phone" and text.lower() == "skip":
                data[field] = "Not shared"
            else:
                data[field] = text

            next_field = next((f for f in FIELDS if f not in data), None)

            if next_field:
                await update.message.reply_text(PROMPTS[next_field])
            else:
                await update.message.reply_text("Send your photos (1–3).")
            return


async def collect_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in temp:
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
    await update.message.forward(chat_id=ADMIN_ID)
    await context.bot.send_message(chat_id=ADMIN_ID, text=caption)

    await update.message.reply_text(
        "✅ Done!\n"
        "If someone liked your profile, we’ll inform you ❤️\n"
        "Admin will contact you if matched."
    )

    # 🔥 DELETE USER DATA IMMEDIATELY
    del temp[uid]


async def notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /notify <user_id>")
        return

    try:
        target_id = int(context.args[0])
        await context.bot.send_message(
            chat_id=target_id,
            text="❤️ Someone liked your profile!\nWe’ll connect you soon."
        )
    except:
        await update.message.reply_text("Invalid user ID.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("notify", notify))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_text))
    app.add_handler(MessageHandler(filters.PHOTO, collect_photo))

    app.run_polling()


if __name__ == "__main__":
    main()

