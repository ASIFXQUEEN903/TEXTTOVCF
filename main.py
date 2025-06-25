import logging
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Document
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
PASSWORD = "BINORI903"
user_auth = {}
user_files = {}

# LOGGING
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 🔧 Helper
def clean_number(number: str) -> str:
    number = number.strip()
    if not number.startswith("+"):
        number = "+" + number
    return number

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

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    service_button = [[InlineKeyboardButton("🗂 Text to VCF Converter", callback_data="access_vcf")]]
    await update.message.reply_text("👇 Tap the service below:", reply_markup=InlineKeyboardMarkup(service_button))

# Password
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_auth[user_id] = False
    await query.message.reply_text("🔑 Enter password to unlock VCF Converter:")

# Handle Text (password or number of files)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # Not registered
    if user_id not in user_auth:
        return

    # Password check
    if user_auth[user_id] is False:
        if text == PASSWORD:
            user_auth[user_id] = True
            await update.message.reply_text("✅ Access granted! Send .txt file now.")
        else:
            await update.message.reply_text("❌ Wrong password. Try again:")
        return

    # After password: user sent how many files
    if user_auth.get(user_id) is True and user_id in user_files:
        try:
            count = int(text)
            all_numbers = user_files.pop(user_id)

            chunks = [all_numbers[i::count] for i in range(count)]

            for i, chunk in enumerate(chunks, 1):
                vcf = create_multi_vcf(chunk)
                filename = f"XQUEEN_PART{i}.vcf"
                with open(filename, "w") as f:
                    f.write(vcf)
                await update.message.reply_document(open(filename, "rb"), caption=f"📁 File {i}")
                os.remove(filename)

        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number.")
        return

# Handle .txt document
async def handle_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_auth or not user_auth[user_id]:
        return

    document = update.message.document
    if not document.file_name.endswith(".txt"):
        await update.message.reply_text("❌ Please upload a .txt file only.")
        return

    file = await context.bot.get_file(document.file_id)
    file_path = f"{user_id}_temp.txt"
    await file.download_to_drive(file_path)

    with open(file_path, "r") as f:
        lines = f.readlines()

    os.remove(file_path)

    numbers = [clean_number(line) for line in lines if line.strip().replace("+", "").isdigit()]

    if not numbers:
        await update.message.reply_text("❌ No valid numbers found in file.")
        return

    user_files[user_id] = numbers
    await update.message.reply_text(f"✅ Found {len(numbers)} numbers.\n\n📤 Now tell me how many .vcf files to split into (e.g., 3, 5, 10):")

# 🔁 Run
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="access_vcf"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_doc))
    print("✅ Bot is running...")
    app.run_polling()
