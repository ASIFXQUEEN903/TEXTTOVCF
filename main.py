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

# 🔐 ENV and Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
PASSWORD = "BINORI903"
OWNER_ID = 7582601826  # Password bypass & /chapass access
user_auth = {}
user_files = {}

# 📋 LOGGING
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ✂️ Clean number and ensure +
def clean_number(number: str) -> str:
    number = number.strip()
    if not number.startswith("+"):
        number = "+" + number
    return number

# 📇 Create VCF
def create_multi_vcf(numbers):
    vcf = ""
    for idx, phone in enumerate(numbers, 1):
        name = f"BINORI {idx}"
        vcf += f"""BEGIN:VCARD
VERSION:3.0
N:{name};;;;
FN:{name}
TEL;TYPE=CELL:{phone}
END:VCARD
"""
    return vcf

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
        caption="👑 Welcome to BINORI's Text ➤ VCF Converter\n🔄 Upload a .txt with numbers and get VCF contacts instantly!",
        reply_markup=InlineKeyboardMarkup(top_buttons)
    )

    service_button = [[InlineKeyboardButton("🗂 Text to VCF Converter", callback_data="access_vcf")]]
    await update.message.reply_text("👇 Tap the service below:", reply_markup=InlineKeyboardMarkup(service_button))

# 🔘 Button: ask password (unless OWNER)
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id == OWNER_ID:
        user_auth[user_id] = True
        await query.message.reply_text("✅ Verified as owner! Send .txt file now.")
    else:
        user_auth[user_id] = False
        await query.message.reply_text("🔑 Enter password to unlock VCF Converter:")

# 📝 Text: either password or file count
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id not in user_auth:
        return

    # 🔑 Password phase
    if user_auth[user_id] is False:
        if text == PASSWORD:
            user_auth[user_id] = True
            await update.message.reply_text("✅ Access granted! Now send .txt file.")
        else:
            await update.message.reply_text("❌ Wrong password. Try again:")
        return

    # 🔢 Count of split files
    if user_auth.get(user_id) and user_id in user_files:
        try:
            count = int(text)
            all_numbers = user_files.pop(user_id)
            chunks = [[] for _ in range(count)]

            # 🔁 Distribute numbers round-robin
            for idx, number in enumerate(all_numbers):
                chunks[idx % count].append(number)

            for i, chunk in enumerate(chunks, 1):
                vcf = create_multi_vcf(chunk)
                filename = f"BINORI_PART_{i}.vcf"
                with open(filename, "w") as f:
                    f.write(vcf)
                await update.message.reply_document(open(filename, "rb"), caption=f"📁 File {i}")
                os.remove(filename)

        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number (like 3, 5, 10).")

# 📄 .txt file handler
async def handle_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_auth or not user_auth[user_id]:
        return

    document = update.message.document
    if not document.file_name.endswith(".txt"):
        await update.message.reply_text("❌ Only .txt files allowed.")
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
    await update.message.reply_text(f"✅ Found {len(numbers)} numbers.\n\n📤 How many .vcf files do you want? (e.g., 3, 5, 10):")

# 🔁 /chapass (owner only)
async def change_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ You're not allowed to use this command.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /chapass NEWPASSWORD")
        return

    global PASSWORD
    PASSWORD = context.args[0]
    await update.message.reply_text(f"✅ Password changed to: `{PASSWORD}`", parse_mode="Markdown")

# ▶️ Main
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="access_vcf"))
    app.add_handler(CommandHandler("chapass", change_password))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_doc))

    print("✅ Bot is running...")
    app.run_polling()
