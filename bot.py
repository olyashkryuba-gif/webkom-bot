import os
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

from texts import T

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", "0"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LANG, NAME, SITE_TYPE, GOAL, PAGES, DESIGN, CONTENT, EXAMPLES, DEADLINE, CONTACT, NOTES, CONFIRM = range(12)


def t(context, key):
    lang = context.user_data.get("lang", "cs")
    return T.get(lang, T["cs"]).get(key, key)


def kb(rows):
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


async def start(update, context):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("Cestina", callback_data="lang_cs"), InlineKeyboardButton("English", callback_data="lang_en")],
        [InlineKeyboardButton("Russian", callback_data="lang_ru"), InlineKeyboardButton("Ukrainian", callback_data="lang_uk")],
    ]
    await update.message.reply_text("Welcome! Choose language:", reply_markup=InlineKeyboardMarkup(keyboard))
    return LANG


async def set_language(update, context):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang
    await query.edit_message_text(t(context, "welcome"))
    await query.message.reply_text(t(context, "ask_name"), reply_markup=ReplyKeyboardRemove())
    return NAME


async def get_name(update, context):
    context.user_data["name"] = update.message.text.strip()
    rows = [[t(context, "site_corp"), t(context, "site_landing")], [t(context, "site_eshop"), t(context, "site_other")]]
    await update.message.reply_text(t(context, "ask_site_type").format(name=context.user_data["name"]), reply_markup=kb(rows))
    return SITE_TYPE


async def get_site_type(update, context):
    context.user_data["site_type"] = update.message.text.strip()
    await update.message.reply_text(t(context, "ask_goal"), reply_markup=ReplyKeyboardRemove())
    return GOAL


async def get_goal(update, context):
    context.user_data["goal"] = update.message.text.strip()
    rows = [[t(context, "pages_1"), t(context, "pages_2_5")], [t(context, "pages_5_10"), t(context, "pages_10_plus")], [t(context, "pages_unknown")]]
    await update.message.reply_text(t(context, "ask_pages"), reply_markup=kb(rows))
    return PAGES


async def get_pages(update, context):
    context.user_data["pages"] = update.message.text.strip()
    rows = [[t(context, "design_have"), t(context, "design_need")], [t(context, "design_inspiration")]]
    await update.message.reply_text(t(context, "ask_design"), reply_markup=kb(rows))
    return DESIGN


async def get_design(update, context):
    context.user_data["design"] = update.message.text.strip()
    rows = [[t(context, "content_have"), t(context, "content_partial")], [t(context, "content_need")]]
    await update.message.reply_text(t(context, "ask_content"), reply_markup=kb(rows))
    return CONTENT


async def get_content(update, context):
    context.user_data["content"] = update.message.text.strip()
    await update.message.reply_text(t(context, "ask_examples"), reply_markup=kb([[t(context, "skip")]]))
    return EXAMPLES


async def get_examples(update, context):
    txt = update.message.text.strip()
    context.user_data["examples"] = "" if txt == t(context, "skip") else txt
    rows = [[t(context, "deadline_asap"), t(context, "deadline_month")], [t(context, "deadline_2_3"), t(context, "deadline_flex")]]
    await update.message.reply_text(t(context, "ask_deadline"), reply_markup=kb(rows))
    return DEADLINE


async def get_deadline(update, context):
    context.user_data["deadline"] = update.message.text.strip()
    await update.message.reply_text(t(context, "ask_contact"), reply_markup=ReplyKeyboardRemove())
    return CONTACT


async def get_contact(update, context):
    context.user_data["contact"] = update.message.text.strip()
    await update.message.reply_text(t(context, "ask_notes"), reply_markup=kb([[t(context, "skip")]]))
    return NOTES


async def get_notes(update, context):
    txt = update.message.text.strip()
    context.user_data["notes"] = "" if txt == t(context, "skip") else txt
    summary = format_summary(context)
    rows = [[t(context, "confirm_send"), t(context, "restart")]]
    await update.message.reply_text(t(context, "summary_intro") + "\n\n" + summary, reply_markup=kb(rows), parse_mode="HTML")
    return CONFIRM


async def confirm(update, context):
    txt = update.message.text.strip()
    if txt == t(context, "restart"):
        await update.message.reply_text(t(context, "restarted"), reply_markup=ReplyKeyboardRemove())
        return await start(update, context)

    user = update.effective_user
    uname = " (@" + user.username + ")" if user.username else ""
    header = "Nova zayavka WebKom\n"
    header += "Vid: " + user.full_name + uname + "\n"
    header += "Chas: " + datetime.now().strftime("%d.%m.%Y %H:%M") + "\n"
    header += "Mova: " + context.user_data.get("lang", "cs").upper() + "\n"
    header += "--------------------\n\n"

    if OWNER_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=header + format_summary(context), parse_mode="HTML")
        except Exception as e:
            logger.error(str(e))

    await update.message.reply_text(t(context, "thanks"), reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    return ConversationHandler.END


async def cancel(update, context):
    msg = t(context, "cancelled") if context.user_data.get("lang") else "Cancelled."
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def format_summary(context):
    d = context.user_data
    lines = []
    lines.append("<b>" + t(context, "sum_name") + ":</b> " + d.get("name", "-"))
    lines.append("<b>" + t(context, "sum_site_type") + ":</b> " + d.get("site_type", "-"))
    lines.append("<b>" + t(context, "sum_goal") + ":</b> " + d.get("goal", "-"))
    lines.append("<b>" + t(context, "sum_pages") + ":</b> " + d.get("pages", "-"))
    lines.append("<b>" + t(context, "sum_design") + ":</b> " + d.get("design", "-"))
    lines.append("<b>" + t(context, "sum_content") + ":</b> " + d.get("content", "-"))
    if d.get("examples"):
        lines.append("<b>" + t(context, "sum_examples") + ":</b> " + d["examples"])
    lines.append("<b>" + t(context, "sum_deadline") + ":</b> " + d.get("deadline", "-"))
    lines.append("<b>" + t(context, "sum_contact") + ":</b> " + d.get("contact", "-"))
    if d.get("notes"):
        lines.append("<b>" + t(context, "sum_notes") + ":</b> " + d["notes"])
    return "\n".join(lines)


def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [CallbackQueryHandler(set_language, pattern=r"^lang_")],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            SITE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_site_type)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
            PAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pages)],
            DESIGN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_design)],
            CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_content)],
            EXAMPLES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_examples)],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_deadline)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_notes)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    logger.info("Bot starting")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
