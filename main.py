import logging
import os
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, Document
)
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PASSWORD = "BINORI903"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

user_auth = {}
user_stage = {}
user_numbers = {}

# 🔄 VCF Creator
def create_multi_vcf(numbers, index):
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
    file_name = f"VCF_PART_{index+1}.vcf"
    with open(file_name, "w") as f:
        f.write(vcf)
    return file_name

# 🚀 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_buttons = [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/WSBINORI"),
            InlineKeyboardButton("👤 Owner", url="https://t.me/B8NORI")
        ]
    ]
    await update.message.reply_photo(
        photo="https://files.catbox.moe/xv5h9a.jpg",
        caption="👑 Welcome to BINORI's Text ➤ VCF Converter\n🔄 Upload a .txt file and convert numbers into VCF files.",
        reply_markup=InlineKeyboardMarkup(top_buttons)
    )
    service_button = [
        [InlineKeyboardButton("🗂 Text to VCF Converter", callback_data="access_vcf")]
    ]
    await update.message.reply_text("👇 Tap the service below:", reply_markup=InlineKeyboardMarkup(service_button))

# 🔘 Button: Ask Password
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_auth[user_id] = False
    user_stage[user_id] = None
    await query.message.reply_text("🔐 Enter password to continue:")

# 🧾 Handle Password / Numbers / File Count
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id not in user_auth:
        return

    # 🔑 Password Check
    if user_auth[user_id] is False:
        if text == PASSWORD:
            user_auth[user_id] = True
            await update.message.reply_text("✅ Access granted! Now send a .txt file containing numbers.")
        else:
            await update.message.reply_text("❌ Wrong password. Try again:")
        return

    # 📄 Stage: Ask for number of files
    if user_stage.get(user_id) == "awaiting_file_count":
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text("❌ Enter a valid number greater than 0:")
            return

        num_files = int(text)
        numbers = user_numbers.get(user_id, [])

        if not numbers:
            await update.message.reply_text("❌ No numbers found. Send the .txt file again.")
            return

        chunk_size = len(numbers) // num_files
        remainder = len(numbers) % num_files
        chunks = []
        start = 0
        for i in range(num_files):
            end = start + chunk_size + (1 if i < remainder else 0)
            chunks.append(numbers[start:end])
            start = end

        # Send all VCF files
        for i, chunk in enumerate(chunks):
            file_name = create_multi_vcf(chunk, i)
            await update.message.reply_document(document=open(file_name, "rb"), caption=f"📄 File {i+1}")
            os.remove(file_name)

        user_stage[user_id] = None
        user_numbers[user_id] = []
        return

    # 🚫 Fallback
    await update.message.reply_text("⚠️ Invalid action. Please upload a .txt file.")

# 📂 Handle .txt upload
async def handle_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not user_auth.get(user_id):
        await update.message.reply_text("❌ You must authenticate first using /start.")
        return

    doc = update.message.document
    if not doc.file_name.endswith(".txt"):
        await update.message.reply_text("❌ Please send a .txt file containing phone numbers.")
        return

    file = await doc.get_file()
    file_path = await file.download_to_drive()

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        numbers = [line.strip() for line in lines if line.strip().startswith("+") and line.strip()[1:].isdigit()]

    os.remove(file_path)

    if not numbers:
        await update.message.reply_text("❌ No valid numbers found in file.")
        return

    user_numbers[user_id] = numbers
    user_stage[user_id] = "awaiting_file_count"
    await update.message.reply_text(f"📄 Total {len(numbers)} numbers found.\n\n🔢 How many VCF files do you want?")

# ▶️ Launch App
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="access_vcf"))
    app.add_handler(MessageHandler(filters.Document.MimeType("text/plain"), handle_doc))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("✅ Bot is running...")
    app.run_polling()
