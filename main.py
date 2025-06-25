import logging import os from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Document from telegram.ext import (ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters)

BOT_TOKEN = os.getenv("BOT_TOKEN") user_states = {}  # user_id: {"authenticated": bool, "step": str, "numbers": list} PASSWORD = "BINORI903"

logging.basicConfig(level=logging.INFO)

def create_multi_vcf(numbers, index): vcf = "" for phone in numbers: last_digits = phone[-4:] name = f"XQUEEN_{last_digits}" vcf += f"""BEGIN:VCARD VERSION:3.0 N:{name};;;; FN:{name} TEL;TYPE=CELL:{phone} END:VCARD """ file_name = f"XQUEEN_PART_{index + 1}.vcf" with open(file_name, "w") as f: f.write(vcf) return file_name

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id user_states[user_id] = {"authenticated": False, "step": "awaiting_password"}

buttons = [
    [InlineKeyboardButton("📢 Channel", url="https://t.me/WSBINORI"),
     InlineKeyboardButton("👤 Owner", url="https://t.me/B8NORI")],
    [InlineKeyboardButton("🗂 Text to VCF Converter", callback_data="access_vcf")]
]

await update.message.reply_photo(
    photo="https://files.catbox.moe/xv5h9a.jpg",
    caption="👑 Welcome to BINORI's Text ➔ VCF Converter\nSend any .txt file with phone numbers to begin.",
    reply_markup=InlineKeyboardMarkup(buttons)
)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query await query.answer() user_id = query.from_user.id user_states[user_id] = {"authenticated": False, "step": "awaiting_password"} await query.message.reply_text("🔑 Enter password to continue:")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id text = update.message.text.strip()

if user_id not in user_states:
    return

state = user_states[user_id]

if state["step"] == "awaiting_password":
    if text == PASSWORD:
        state["authenticated"] = True
        state["step"] = "awaiting_file"
        await update.message.reply_text("✅ Access granted! Now send a .txt file with phone numbers.")
    else:
        await update.message.reply_text("❌ Wrong password. Try again:")

elif state["step"] == "awaiting_file":
    await update.message.reply_text("📂 Please send a .txt file with phone numbers (one per line).")

elif state["step"] == "awaiting_file_count":
    if text.isdigit():
        count = int(text)
        numbers = state["numbers"]
        chunks = [numbers[i::count] for i in range(count)]

        for idx, part in enumerate(chunks):
            file_path = create_multi_vcf(part, idx)
            await update.message.reply_document(document=open(file_path, "rb"), caption=f"✅ Part {idx + 1}")
            os.remove(file_path)

        state["step"] = "done"
    else:
        await update.message.reply_text("❌ Please enter a valid number of files.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.effective_user.id state = user_states.get(user_id)

if not state or not state.get("authenticated"):
    return

if update.message.document.mime_type != "text/plain":
    await update.message.reply_text("❌ Only .txt files are supported.")
    return

file = await update.message.document.get_file()
content = await file.download_as_bytearray()
lines = content.decode("utf-8").splitlines()
numbers = [line.strip() for line in lines if line.strip().startswith("+") and line.strip()[1:].isdigit()]

if not numbers:
    await update.message.reply_text("❌ No valid phone numbers found in file.")
    return

user_states[user_id]["numbers"] = numbers
user_states[user_id]["step"] = "awaiting_file_count"
await update.message.reply_text(f"📄 Total {len(numbers)} numbers found. How many .vcf files do you want?")

if name == "main": app = ApplicationBuilder().token(BOT_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(CallbackQueryHandler(button_click, pattern="access_vcf")) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)) app.add_handler(MessageHandler(filters.Document.ALL, handle_document)) print("✅ Bot is running...") app.run_polling()

