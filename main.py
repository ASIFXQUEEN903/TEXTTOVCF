import logging
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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
user_files = {}

# 📋 Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ➕ Add "+" if missing
def clean_number(number: str) -> str:
    number = number.strip()
    return number if number.startswith("+") else "+" + number

# 📁 VCF Generator
def create_vcf_chunk(numbers, start_index):
    vcf = ""
    for i, phone in enumerate(numbers, start=start_index):
        name = f"BINORI {i}"
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
        caption="👑 Welcome to BINORI's Text ➤ VCF Converter\n🔄 Send phone numbers and get .vcf contact file instantly!",
        reply_markup=InlineKeyboardMarkup(top_buttons)
    )
    service_button = [[InlineKeyboardButton("🗂 Text to VCF Converter", callback_data="access_vcf")]]
    await update.message.reply_text("👇 Tap the service below:", reply_markup=InlineKeyboardMarkup(service_button))

# 🔘 Button Click → Ask for Password
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_auth[user_id] = False
    await query.message.reply_text("🔑 Enter password to unlock VCF Converter:")

# ✉️ Handle password or number of files
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id not in user_auth:
        return

    # 🛡 Password checking
    if user_auth[user_id] is False:
        if text == PASSWORD:
            user_auth[user_id] = True
            await update.message.reply_text("✅ Access granted! Now send a .txt file containing phone numbers.")
        else:
            await update.message.reply_text("❌ Wrong password. Try again:")
        return

    # 🔢 After password: handle number of output files
    if user_auth.get(user_id) is True and user_id in user_files:
        try:
            file_count = int(text)
            numbers = user_files.pop(user_id)
            total = len(numbers)

            chunk_size = total // file_count
            remainder = total % file_count

            files = []
            index = 0
            for i in range(file_count):
                extra = 1 if i < remainder else 0
                chunk = numbers[index:index + chunk_size + extra]
                vcf = create_vcf_chunk(chunk, index + 1)
                filename = f"BINORI_{i+1}.vcf"
                with open(filename, "w") as f:
                    f.write(vcf)
                files.append(filename)
                index += len(chunk)

            for f in files:
                await update.message.reply_document(document=open(f, "rb"), caption=f"📁 {f}")
                os.remove(f)

            await update.message.reply_text("✅ All files sent successfully.")

        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number.")
        return

# 📄 Handle .txt file
async def handle_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_auth or not user_auth[user_id]:
        return

    doc = update.message.document
    if not doc.file_name.endswith(".txt"):
        await update.message.reply_text("❌ Please upload a `.txt` file only.")
        return

    file = await context.bot.get_file(doc.file_id)
    temp = f"{user_id}_temp.txt"
    await file.download_to_drive(temp)

    with open(temp, "r") as f:
        lines = f.readlines()

    os.remove(temp)

    numbers = [clean_number(line) for line in lines if line.strip().replace("+", "").isdigit()]
    if not numbers:
        await update.message.reply_text("❌ No valid numbers found in file.")
        return

    user_files[user_id] = numbers
    await update.message.reply_text(f"✅ {len(numbers)} numbers found.\nNow tell me how many .vcf files you want:")

# ▶️ Launch bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="access_vcf"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_doc))
    print("✅ Bot is running...")
    app.run_polling()
