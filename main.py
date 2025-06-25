import logging
import os
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# 🔐 Env variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
PASSWORD = "BINORI903"
user_auth = {}

# 📋 Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 📞 VCF Generator
def create_multi_vcf(numbers):
    vcf = ""
    for phone in numbers:
        last_digits = phone[-4:]
        name = f"XQUEEN_{last_digits}"
        vcf += f"""BEGIN:VCARD
VERSION:3.0
N:{name};;;;
FN:{name}
TEL;TYPE=CELL:{phone}
END:VCARD
"""
    return vcf

# 🚀 /start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Image + 2 buttons
    top_buttons = [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/WSBINORI"),
            InlineKeyboardButton("👤 Owner", url="https://t.me/B8NORI")
        ]
    ]
    await update.message.reply_photo(
        photo="https://files.catbox.moe/xv5h9a.jpg",
        caption="👑 Welcome to BINORI's Text ➤ VCF Converter\n🔄 Send phone numbers and get .vcf contact file instantly!",
        reply_markup=InlineKeyboardMarkup(top_buttons)
    )

    # Telegram services-style single line button
    service_button = [
        [InlineKeyboardButton("🗂 Text to VCF Converter", callback_data="access_vcf")]
    ]
    await update.message.reply_text("👇 Tap the service below:", reply_markup=InlineKeyboardMarkup(service_button))

# 🔘 Button Callback (asks password)
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_auth[user_id] = False
    await query.message.reply_text("🔑 Enter password to unlock VCF Converter:")

# ✉️ Handle both password & number input
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id not in user_auth:
        return

    if user_auth[user_id] is False:
        if text == PASSWORD:
            user_auth[user_id] = True
            await update.message.reply_text("✅ Access granted! Now send phone numbers to get VCF file.")
        else:
            await update.message.reply_text("❌ Wrong password. Try again:")
        return

    # If access granted: handle numbers
    if user_auth.get(user_id):
        numbers = [
            line.strip() for line in text.split("\n")
            if line.strip().startswith("+") and line.strip()[1:].isdigit()
        ]
        if not numbers:
            await update.message.reply_text("❌ Send valid phone numbers (one per line, starting with +)")
            return

        vcf_content = create_multi_vcf(numbers)
        file_name = "XQUEEN_CONTACTS.vcf"
        with open(file_name, "w") as f:
            f.write(vcf_content)

        await update.message.reply_document(document=open(file_name, "rb"), caption=f"✅ {len(numbers)} contacts saved")
        os.remove(file_name)

# 🔁 App launcher
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="access_vcf"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("✅ Bot is running...")
    app.run_polling()
