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
uploaded_data = {}  # user_id: list of numbers
ask_count = {}      # user_id: bool waiting for count input

# ✅ Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 🔄 VCF Generator
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
    top_buttons = [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/WSBINORI"),
            InlineKeyboardButton("👤 Owner", url="https://t.me/B8NORI")
        ]
    ]
    await update.message.reply_photo(
        photo="https://files.catbox.moe/xv5h9a.jpg",
        caption="👑 Welcome to BINORI's Text ➤ VCF Converter\n🔄 Upload your .txt number file and get multiple VCFs!",
        reply_markup=InlineKeyboardMarkup(top_buttons)
    )
    service_button = [
        [InlineKeyboardButton("🗂 Text to VCF Converter", callback_data="access_vcf")]
    ]
    await update.message.reply_text("👇 Tap the service below:", reply_markup=InlineKeyboardMarkup(service_button))

# 🔘 Button Click
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_auth[user_id] = False
    await query.message.reply_text("🔑 Enter password to unlock VCF Converter:")

# 🧠 Text Handler
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # Asking for password
    if user_id in user_auth and user_auth[user_id] is False:
        if text == PASSWORD:
            user_auth[user_id] = True
            await update.message.reply_text("✅ Access granted! Now send your .txt number file.")
        else:
            await update.message.reply_text("❌ Wrong password. Try again:")
        return

    # Asking how many files to split into
    if ask_count.get(user_id):
        if text.isdigit() and int(text) > 0:
            count = int(text)
            nums = uploaded_data[user_id]
            chunk_size = len(nums) // count
            extras = len(nums) % count

            index = 0
            for i in range(count):
                end = index + chunk_size + (1 if i < extras else 0)
                chunk = nums[index:end]
                vcf = create_multi_vcf(chunk)
                file_name = f"contacts_{i+1}.vcf"
                with open(file_name, "w") as f:
                    f.write(vcf)
                await update.message.reply_document(document=open(file_name, "rb"), caption=f"📁 File {i+1} — {len(chunk)} contacts")
                os.remove(file_name)
                index = end

            ask_count[user_id] = False
            uploaded_data.pop(user_id, None)
        else:
            await update.message.reply_text("❌ Invalid number. Please enter a valid count (e.g. 3):")

# 📂 Document (.txt) Handler
async def handle_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not user_auth.get(user_id):
        await update.message.reply_text("🚫 Access denied. Use /start and unlock access first.")
        return

    doc = update.message.document
    if doc.mime_type != "text/plain":
        await update.message.reply_text("❌ Please upload a valid .txt file only.")
        return

    file = await doc.get_file()
    downloaded = await file.download_to_drive()
    with open(downloaded, "r", encoding="utf-8") as f:
        content = f.readlines()

    numbers = [
        line.strip() for line in content
        if line.strip().startswith("+") and line.strip()[1:].isdigit()
    ]

    if not numbers:
        await update.message.reply_text("❌ No valid numbers found in the file.")
        return

    uploaded_data[user_id] = numbers
    ask_count[user_id] = True
    await update.message.reply_text(f"✅ Loaded {len(numbers)} numbers.\n📌 How many VCF files do you want?")

# 🔁 Start Bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="access_vcf"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.MIME_TYPE("text/plain"), handle_doc))
    print("✅ Bot is running...")
    app.run_polling()
