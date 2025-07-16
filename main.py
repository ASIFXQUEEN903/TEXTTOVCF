import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PASSWORD = "BINORI903"
OWNER_ID = 5826711802

user_auth = {}
user_files = {}
user_steps = {}
user_seen_start = {}  # Track welcome shown

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def clean_number(number: str) -> str:
    number = number.strip()
    if not number.startswith("+"):
        number = "+" + number
    return number

async def send_welcome(user_id, context):
    await context.bot.send_photo(
        chat_id=user_id,
        photo="https://files.catbox.moe/xv5h9a.jpg",
        caption="👑 Welcome to BINORI's Text ➤ VCF Converter\n\n🔄 Upload a `.txt` file or paste numbers manually.\n📤 Then get VCF contacts instantly!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Channel", url="https://t.me/WSBINORI"),
             InlineKeyboardButton("👤 Owner", url="https://t.me/B8NORI")]
        ])
    )
    await context.bot.send_message(
        chat_id=user_id,
        text="👇 Tap the service below:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗂 Text to VCF Converter", callback_data="access_vcf")]
        ])
    )

# 🚀 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member("@WSBINORI", user_id)
        if member.status in ["left", "kicked"]:
            raise Exception("Not joined")
    except:
        await update.message.reply_text(
            "🚫 Access Denied!\n\n👋 Please join our official channel to use this bot.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url="https://t.me/WSBINORI")],
                [InlineKeyboardButton("✅ I’ve Joined", callback_data="access_vcf")]
            ])
        )
        return
    user_seen_start[user_id] = True
    await send_welcome(user_id, context)

# 🔘 Button Handler
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    try:
        member = await context.bot.get_chat_member("@WSBINORI", user_id)
        if member.status in ["left", "kicked"]:
            raise Exception("Not joined")
    except:
        await query.message.reply_text(
            "🚫 Still not joined.\n\nPlease join the channel to continue.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url="https://t.me/WSBINORI")],
                [InlineKeyboardButton("✅ I’ve Joined", callback_data="access_vcf")]
            ])
        )
        return

    if not user_seen_start.get(user_id):
        user_seen_start[user_id] = True
        await send_welcome(user_id, context)
        return

    if user_id == OWNER_ID:
        user_auth[user_id] = True
        await context.bot.send_message(user_id, "✅ Verified as owner! Send .txt file or paste numbers manually.")
    else:
        if not user_auth.get(user_id):
            user_auth[user_id] = False
        await context.bot.send_message(user_id, "🔑 Enter password to unlock VCF Converter:")

# 📝 Text Handler
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id not in user_auth:
        return

    if user_auth[user_id] is False:
        if text == PASSWORD:
            user_auth[user_id] = True
            await update.message.reply_text("✅ Access granted! Now send .txt file or paste numbers manually.")
        else:
            await update.message.reply_text("❌ Wrong password. Try again:")
        return

    if user_id not in user_files and user_id not in user_steps:
        lines = text.split("\n")
        numbers = [clean_number(line) for line in lines if line.strip().replace("+", "").isdigit()]
        if numbers:
            user_files[user_id] = numbers
            await update.message.reply_text(f"✅ Found {len(numbers)} numbers.\n\n📤 How many .vcf files do you want? (e.g., 3, 5, 10):")
            return

    if user_id in user_files and user_id not in user_steps:
        try:
            count = int(text)
            if count <= 0:
                raise ValueError
            user_steps[user_id] = {"count": count}
            await update.message.reply_text("📝 Great! Now send the file name (e.g. QueenList):")
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number (like 3, 5, 10).")
        return

    if user_id in user_steps:
        info = user_steps.pop(user_id)
        count = info["count"]
        all_numbers = user_files.pop(user_id)
        chunks = [[] for _ in range(count)]

        for idx, number in enumerate(all_numbers):
            chunks[idx % count].append(number)

        contact_index = 1
        base_name = text.replace(" ", "_")
        for i, chunk in enumerate(chunks, 1):
            vcf = ""
            for phone in chunk:
                name = f"{base_name} {contact_index}"
                vcf += f"""BEGIN:VCARD
VERSION:3.0
N:{name};;;;
FN:{name}
TEL;TYPE=CELL:{phone}
END:VCARD
"""
                contact_index += 1

            filename = f"{base_name}_{i}.vcf"
            with open(filename, "w") as f:
                f.write(vcf)
            await update.message.reply_document(open(filename, "rb"), caption=f"📁 {filename} | {len(chunk)} contacts")
            os.remove(filename)

# 📂 .txt file handler
async def handle_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not user_auth.get(user_id):
        return

    doc = update.message.document
    if not doc.file_name.endswith(".txt"):
        await update.message.reply_text("❌ Only .txt files allowed.")
        return

    file_path = f"{user_id}_temp.txt"
    file = await context.bot.get_file(doc.file_id)
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

# 🔁 /chapass command
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
    app.add_handler(CommandHandler("chapass", change_password))
    app.add_handler(CallbackQueryHandler(handle_button, pattern="access_vcf"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_doc))

    print("✅ Bot is running...")
    app.run_polling()
