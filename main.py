import logging
import os
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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

# ✅ /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔗 Owner", url="https://t.me/B8NORI")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Hey I am personal text to VCF converter of BINORI",
        reply_markup=reply_markup
    )

# ✅ text message handler
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.strip()
    numbers = [line.strip() for line in raw.split("\n") if line.strip().startswith("+") and line.strip()[1:].isdigit()]

    if not numbers:
        await update.message.reply_text("❌ Send valid phone numbers (one per line, starting with +)")
        return

    vcf_content = create_multi_vcf(numbers)
    file_name = "XQUEEN_CONTACTS.vcf"

    with open(file_name, "w") as f:
        f.write(vcf_content)

    await update.message.reply_document(document=open(file_name, "rb"), caption=f"✅ {len(numbers)} contacts saved")
    os.remove(file_name)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("✅ Bot is running... (Heroku or Termux ready)")
    app.run_polling()
