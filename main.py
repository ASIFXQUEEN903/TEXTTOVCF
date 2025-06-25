import logging
import os
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Document
)
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PASSWORD = "BINORI903"

user_auth = {}
user_stage = {}
user_txt_numbers = {}

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Generate VCF
def create_multi_vcf(numbers, index):
    vcf = ""
    for phone in numbers:
        last_digits = phone[-4:]
        name = f"XQUEEN_{last_digits}_{index}"
        vcf += f"""BEGIN:VCARD
VERSION:3.0
N:{name};;;;
FN:{name}
TEL;TYPE=CELL:{phone}
END:VCARD
"""
    return vcf

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_buttons = [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/WSBINORI"),
            InlineKeyboardButton("👤 Owner", url="https://t.me/B8NORI")
        ]
    ]
    await update.message.reply_photo(
        photo="https://files.catbox.moe/xv5h9a.jpg",
        caption="👑 Welcome to BINORI's Text ➤ VCF Converter\n🔄 Upload .txt file of phone numbers, convert to multiple VCFs.",
        reply_markup=InlineKeyboardMarkup(top_buttons)
    )

    service_button = [
        [InlineKeyboardButton("🗂 Text to VCF Converter", callback_data="access_vcf")]
    ]
    await update.message.reply_text("👇 Tap the service below:", reply_markup=InlineKeyboardMarkup(service_button))

# Button press → ask password
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_auth[user_id] = False
    user_stage[user_id] = "awaiting_password"
    await query.message.reply_text("🔑 Enter password to unlock VCF Converter:")

# Handle password / numbers / file count
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # If no stage, ignore
    if user_id not in user_stage:
        return

    # Password stage
    if user_stage[user_id] == "awaiting_password":
        if text == PASSWORD:
            user_auth[user_id] = True
            user_stage[user_id] = "ready_for_txt"
            await update.message.reply_text("✅ Access granted! Now send a `.txt` file with numbers.")
        else:
            await update.message.reply_text("❌ Wrong password. Try again:")
        return

    # File count stage
    if user_stage[user_id] == "awaiting_file_count":
        if not text.isdigit():
            await update.message.reply_text("❌ Send a valid number (how many files you want).")
            return

        num_parts = int(text)
        numbers = user_txt_numbers.get(user_id, [])

        if not numbers:
            await update.message.reply_text("❌ No phone numbers found.")
            return

        chunk_size = len(numbers) // num_parts
        for i in range(num_parts):
            start = i * chunk_size
            end = None if i == num_parts - 1 else (i + 1) * chunk_size
            chunk = numbers[start:end]
            vcf_content = create_multi_vcf(chunk, i+1)
            filename = f"XQUEEN_PART_{i+1}.vcf"
            with open(filename, "w") as f:
                f.write(vcf_content)
            await update.message.reply_document(document=open(filename, "rb"), caption=f"✅ File {i+1} of {num_parts}")
            os.remove(filename)

        await update.message.reply_text("🎉 All VCF files sent!")
        user_stage[user_id] = "ready_for_txt"
        return

# Handle .txt file
async def handle_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not user_auth.get(user_id):
        return

    file = update.message.document
    if not file.file_name.endswith(".txt"):
        await update.message.reply_text("❌ Please send a `.txt` file only.")
        return

    file_path = f"{user_id}_temp.txt"
    await file.get_file().download_to_drive(file_path)

    with open(file_path, "r") as f:
        numbers = [line.strip() for line in f if line.strip().startswith("+") and line.strip()[1:].isdigit()]

    os.remove(file_path)

    if not numbers:
        await update.message.reply_text("❌ No valid phone numbers found in file.")
        return

    user_txt_numbers[user_id] = numbers
    user_stage[user_id] = "awaiting_file_count"
    await update.message.reply_text(f"📄 Found {len(numbers)} numbers. How many VCF files do you want?")

# Run app
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="access_vcf"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.FILE_EXTENSION("txt"), handle_doc))
    print("✅ Bot is running...")
    app.run_polling()
