from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_USERNAME = "Mind_game76"

user_data_temp = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp[update.effective_user.id] = {}
    await update.message.reply_text("Enter your name:")

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    data = user_data_temp.get(uid, {})

    steps = ["name", "age", "language", "phone", "looking_for", "bio"]
    for step in steps:
        if step not in data:
            data[step] = text
            user_data_temp[uid] = data
            await update.message.reply_text(f"Enter {steps[steps.index(step)+1] if step != 'bio' else 'send your photos'}:")
            return

async def photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = user_data_temp.get(uid)

    admin = f"@{ADMIN_USERNAME}"
    caption = (
        f"📩 New Profile\n\n"
        f"Name: {data['name']}\n"
        f"Age: {data['age']}\n"
        f"Language: {data['language']}\n"
        f"Phone: {data['phone']}\n"
        f"Looking for: {data['looking_for']}\n"
        f"Bio: {data['bio']}"
    )

    await update.message.forward(chat_id=admin)
    await update.message.reply_text(
        "✅ Done!\nIf someone liked your profile, we’ll inform you.\nAdd admin to contacts."
    )

    user_data_temp.pop(uid, None)  # DELETE DATA

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect))
    app.add_handler(MessageHandler(filters.PHOTO, photos))
    app.run_polling()

if __name__ == "__main__":
    main()
