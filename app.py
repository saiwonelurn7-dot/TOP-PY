import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from supabase import create_client, Client

# ====================== သင့်အချက်အလက်များ ထည့်ပါ ======================
BOT_TOKEN = "8761072743:AAG9klC1yLxEUAttBTBO1klBW9LgOz2WRLM"               # @BotFather ဆီက ရထားတာ
CHANNEL_ID = -1004409384544                # @getidsbot ဆီက ရထားတဲ့ နံပါတ် ( - ပါပါ )
CHANNEL_USERNAME = "@topvideo231" # Channel Username ( @ ပါပါ )
SUPABASE_URL = "https://arrhwehhmouwveszexln.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFycmh3ZWhobW91d3Zlc3pleGxuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM4MzY2NzMsImV4cCI6MjA5OTQxMjY3M30.fX8xpA5yhMnlOfaVB_vhHO_vdBkXo8z8Q-5Nzzfsm6Q"
ADMIN_USER_ID = 8747661185                  # သင့်ရဲ့ Telegram User ID
# ====================================================================

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Conversation States (အဆင့် ၃ ဆင့်)
TITLE, DESCRIPTION, VIDEO = range(3)

# ---------- /cancel Command ----------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ လုပ်ဆောင်ချက်ကို ဖျက်သိမ်းလိုက်ပါပြီ။")
    return ConversationHandler.END

# ---------- ၁။ /add ကိုနှိပ်ရင် Title မေးမယ် ----------
async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ သင့်မှာ ဒီ Command ကိုသုံးခွင့်မရှိပါ။")
        return ConversationHandler.END

    await update.message.reply_text(
        "🎬 ဗီဒီယိုအသစ်ထည့်ခြင်း (စတင်ပါပြီ)\n"
        "အဆင့် ၁/၃ - ဗီဒီယိုနာမည် (Title) ကို ရိုက်ထည့်ပါ။\n"
        "(မလုပ်ချင်ရင် /cancel နှိပ်ပါ)"
    )
    return TITLE

# ---------- ၂။ Title ရပြီ → Description မေးမယ် ----------
async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    context.user_data['title'] = title

    await update.message.reply_text(
        f"✅ Title: {title}\n\n"
        "အဆင့် ၂/၃ - ဖော်ပြချက် (Description) ကို ရိုက်ထည့်ပါ။\n"
        "(မထည့်ချင်ရင် 'skip' လို့ရိုက်ပါ)"
    )
    return DESCRIPTION

# ---------- ၃။ Description ရပြီ → Video မေးမယ် ----------
async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    if description.lower() == 'skip':
        description = ""
    context.user_data['description'] = description

    await update.message.reply_text(
        f"✅ Description: {description if description else '(ဗလာ)'}\n\n"
        "အဆင့် ၃/၃ - Video ဖိုင် (MP4) ကို Upload တင်ပါ။\n"
        "👉 Video ကိုသာ တင်ပေးပါ။"
    )
    return VIDEO

# ---------- ၄။ Video ရပြီ → Channel နဲ့ Database ကိုသိမ်းမယ် ----------
async def get_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.video:
        await update.message.reply_text("❌ Video ဖိုင် (MP4) ကိုပဲ တင်ပေးပါ။ /add ပြန်နှိပ်ပါ။")
        return VIDEO

    video = update.message.video
    file_id = video.file_id
    title = context.user_data.get('title', 'No Title')
    description = context.user_data.get('description', '')

    # --- ၁။ Video ကို Channel ထဲ Post လုပ်မယ် ---
    try:
        caption = f"🎬 {title}\n\n📝 {description}" if description else f"🎬 {title}"
        sent_message = await context.bot.send_video(
            chat_id=CHANNEL_ID,
            video=file_id,
            caption=caption,
            protect_content=False
        )
        post_link = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}/{sent_message.message_id}"
    except Exception as e:
        await update.message.reply_text(f"❌ Channel မှာ Post မတင်နိုင်ဘူး။ Error: {e}")
        return ConversationHandler.END

    # --- ၂။ Database ထဲကို သိမ်းမယ် ---
    try:
        data, count = supabase.table("movies").insert({
            "title": title,
            "description": description,
            "file_id": file_id,
            "channel_link": post_link
        }).execute()

        await update.message.reply_text(
            f"✅ အောင်မြင်ပါပြီ!\n"
            f"🎬 {title}\n"
            f"📝 {description if description else '(မရှိ)'}\n"
            f"🔗 {post_link}\n\n"
            "Website ပေါ်မှာ အလိုအလျောက် ပေါ်လာပါပြီ။"
        )
        context.user_data.clear()
        return ConversationHandler.END

    except Exception as e:
        await update.message.reply_text(f"❌ Database မှာ သိမ်းလို့မရဘူး။ Error: {e}")
        return ConversationHandler.END

# ---------- Bot ကို Run ခြင်း ----------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', start_add)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            VIDEO: [MessageHandler(filters.VIDEO, get_video)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
