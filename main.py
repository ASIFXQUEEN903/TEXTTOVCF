import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.constants import ChatType
from telegram.error import BadRequest
from pymongo import MongoClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
MONGO_URL = os.getenv("MONGO_URL")

mongo = MongoClient(MONGO_URL)
db = mongo["vcfbot"]
auth_col = db["auth_users"]
pass_col = db["password"]
user_col = db["broadcast_users"]

logging.basicConfig(level=logging.INFO)

def clean_number(number: str) -> str:
    number = number.strip()
    if not number.startswith("+"):
        number = "+" + number
    return number

def get_password():
    data = pass_col.find_one({"_id": "password"})
    return data["value"] if data else "BINORI903"

def set_password(new_pass):
    pass_col.update_one({"_id": "password"}, {"$set": {"value": new_pass}}, upsert=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_col.update_one({"_id": user_id}, {"$set": {}}, upsert=True)

    try:
        member = await context.bot.get_chat_member("@WSBINORI", user_id)
        if member.status in ["left", "kicked"]:
            raise Exception("Not joined")
    except:
        await update.message.reply_text(
            "🚫 Please join our channel to access this bot.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url="https://t.me/WSBINORI")],
                [InlineKeyboardButton("✅ I’ve Joined", url="https://t.me/atokick_ws_bot?start=_")]
            ])
        )
        return

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

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    is_owner_or_sudo = user_id == OWNER_ID or auth_col.find_one({"_id": user_id})
    if not is_owner_or_sudo:
        await query.message.reply_text("🔑 Enter password to unlock VCF Converter:")
        context.user_data["awaiting_pass"] = True
        return

    context.user_data["auth"] = True
    await query.message.reply_text("✅ You are verified! Now send .txt file or paste numbers.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if context.user_data.get("awaiting_pass"):
        if text == get_password():
            context.user_data["auth"] = True
            auth_col.update_one({"_id": user_id}, {"$set": {}}, upsert=True)
            await update.message.reply_text("✅ Access granted! Now send .txt file or paste numbers.")
        else:
            await update.message.reply_text("❌ Wrong password. Try again:")
        context.user_data["awaiting_pass"] = False
        return

    if not context.user_data.get("auth") and user_id != OWNER_ID:
        return

    if "numbers" not in context.user_data:
        lines = text.split("\n")
        numbers = [clean_number(line) for line in lines if line.strip().replace("+", "").isdigit()]
        if numbers:
            context.user_data["numbers"] = numbers
            await update.message.reply_text(f"📞 Found {len(numbers)} numbers.\nHow many VCF files? (e.g., 3, 5):")
        return
    elif "count" not in context.user_data:
        try:
            count = int(text)
            context.user_data["count"] = count
            await update.message.reply_text("📝 Send base filename (e.g. QueenList):")
        except:
            await update.message.reply_text("❌ Enter valid number.")
        return
    else:
        count = context.user_data["count"]
        numbers = context.user_data["numbers"]
        filename = text.strip().replace(" ", "_")
        chunks = [[] for _ in range(count)]

        for i, num in enumerate(numbers):
            chunks[i % count].append(num)

        index = 1
        for i, chunk in enumerate(chunks, 1):
            vcf = ""
            for phone in chunk:
                name = f"{filename} {index}"
                vcf += f"""BEGIN:VCARD
VERSION:3.0
N:{name};;;;
FN:{name}
TEL;TYPE=CELL:{phone}
END:VCARD
"""
                index += 1
            file_name = f"{filename}_{i}.vcf"
            with open(file_name, "w") as f:
                f.write(vcf)
            await update.message.reply_document(open(file_name, "rb"), caption=f"📁 {file_name}")
            os.remove(file_name)

        context.user_data.clear()

async def handle_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.user_data.get("auth") and user_id != OWNER_ID:
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
        await update.message.reply_text("❌ No valid numbers found.")
        return

    context.user_data["numbers"] = numbers
    await update.message.reply_text(f"✅ Found {len(numbers)} numbers.\nHow many VCF files?")

async def change_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ You’re not authorized.")
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /chapass NEWPASS")
    set_password(context.args[0])
    await update.message.reply_text(f"✅ Password changed to: `{context.args[0]}`", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Unauthorized.")
    if update.message.reply_to_message:
        target = update.message.reply_to_message
    else:
        if not context.args:
            return await update.message.reply_text("⚠️ Reply to a message or use: /broadcast Hello users!")
        text = " ".join(context.args)
        target = await update.message.reply_text("✅ Broadcasting...")

    total = 0
    failed = 0
    users = user_col.find()
    for u in users:
        try:
            await target.copy(chat_id=u["_id"])
            total += 1
            await asyncio.sleep(0.5)
        except:
            failed += 1

    await update.message.reply_text(f"📤 Sent: {total} | ❌ Failed: {failed}")

async def get_user_id_from_input(input_text, context):
    if input_text.isdigit():
        return int(input_text)
    if input_text.startswith("@"):
        input_text = input_text[1:]
    try:
        user = await context.bot.get_chat(input_text)
        if user.type == ChatType.PRIVATE:
            return user.id
    except BadRequest:
        return None
    return None

async def add_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ You’re not authorized.")
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /addsudo <username or user_id>")

    user_id = await get_user_id_from_input(context.args[0], context)
    if not user_id:
        return await update.message.reply_text("❌ Invalid user.")
    auth_col.update_one({"_id": user_id}, {"$set": {}}, upsert=True)
    await update.message.reply_text(f"✅ Sudo added for user ID `{user_id}`", parse_mode="Markdown")

async def rm_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ You’re not authorized.")
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /rmsudo <username or user_id>")

    user_id = await get_user_id_from_input(context.args[0], context)
    if not user_id:
        return await update.message.reply_text("❌ Invalid user.")
    auth_col.delete_one({"_id": user_id})
    await update.message.reply_text(f"✅ Sudo removed for user ID `{user_id}`", parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_doc))
    app.add_handler(CommandHandler("chapass", change_pass))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("addsudo", add_sudo))
    app.add_handler(CommandHandler("rmsudo", rm_sudo))
    print("✅ Bot running...")
    app.run_polling()
