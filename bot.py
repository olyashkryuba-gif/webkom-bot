import os
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

from texts import T

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", "0"))
WELCOME_PHOTO = "welcome.png"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LANG, NAME_CONFIRM, NAME, SITE_TYPE, GOAL, GOAL_TEXT, PAGES, DESIGN, CONTENT, EXAMPLES, DEADLINE, CONTACT, CONTACT_TEXT, NOTES, NOTES_TEXT, CONFIRM = range(16)


def t(context, key):
    lang = context.user_data.get("lang", "cs")
    return T.get(lang, T["cs"]).get(key, key)


def kb(rows):
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


async def send(update, text, reply_markup=None):
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")


async def start(update, context):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("🇨🇿 Cestina", callback_data="lang_cs"), InlineKeyboardButton("🇬 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"), InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk")],
    ]
    try:
        with open(WELCOME_PHOTO, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="<b>WebKom</b> 👋\n\nWelcome! • Vitejte! • Добро пожаловать! • Вітаємо!",
                parse_mode="HTML",
            )
    except FileNotFoundError:
        logger.warning("welcome.png not found, skipping photo")
    await update.message.reply_text(
        "Please choose your language / Vyberte jazyk:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return LANG


async def set_language(update, context):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang
    await query.edit_message_text(t(context, "welcome"), parse_mode="HTML")

    user = query.from_user
    detected_name = user.first_name or ""
    if user.last_name:
        detected_name += " " + user.last_name
    detected_name = detected_name.strip()

    if detected_name:
        context.user_data["detected_name"] = detected_name
        rows = [[t(context, "name_yes"), t(context, "name_change")]]
        await query.message.reply_text(
            t(context, "ask_name_confirm").format(name=detected_name),
            reply_markup=kb(rows),
            parse_mode="HTML",
        )
        return NAME_CONFIRM
    else:
        await query.message.reply_text(t(context, "ask_name"), reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        return NAME


async def name_confirm(update, context):
    txt = update.message.text.strip()
    if txt == t(context, "name_yes"):
        context.user_data["name"] = context.user_data.get("detected_name", "")
        return await go_site_type(update, context)
    else:
        await send(update, t(context, "ask_name"), ReplyKeyboardRemove())
        return NAME


async def get_name(update, context):
    context.user_data["name"] = update.message.text.strip()
    return await go_site_type(update, context)


async def go_site_type(update, context):
    rows = [[t(context, "site_corp"), t(context, "site_landing")], [t(context, "site_eshop"), t(context, "site_other")]]
    await send(update, t(context, "ask_site_type").format(name=context.user_data["name"]), kb(rows))
    return SITE_TYPE


async def get_site_type(update, context):
    context.user_data["site_type"] = update.message.text.strip()
    rows = [
        [t(context, "goal_leads"), t(context, "goal_sell")],
        [t(context, "goal_present"), t(context, "goal_orders")],
        [t(context, "goal_other")],
    ]
    await send(update, t(context, "ask_goal"), kb(rows))
    return GOAL


async def get_goal(update, context):
    txt = update.message.text.strip()
    if txt == t(context, "goal_other"):
        await send(update, t(context, "ask_goal_text"), ReplyKeyboardRemove())
        return GOAL_TEXT
    context.user_data["goal"] = txt
    return await go_pages(update, context)


async def get_goal_text(update, context):
    context.user_data["goal"] = update.message.text.strip()
    return await go_pages(update, context)


async def go_pages(update, context):
    rows = [[t(context, "pages_1"), t(context, "pages_2_5")], [t(context, "pages_5_10"), t(context, "pages_10_plus")], [t(context, "pages_unknown")]]
    await send(update, t(context, "ask_pages"), kb(rows))
    return PAGES


async def get_pages(update, context):
    context.user_data["pages"] = update.message.text.strip()
    rows = [[t(context, "design_have"), t(context, "design_need")], [t(context, "design_inspiration")]]
    await send(update, t(context, "ask_design"), kb(rows))
    return DESIGN


async def get_design(update, context):
    context.user_data["design"] = update.message.text.strip()
    rows = [[t(context, "content_have"), t(context, "content_partial")], [t(context, "content_need")]]
    await send(update, t(context, "ask_content"), kb(rows))
    return CONTENT


async def get_content(update, context):
    context.user_data["content"] = update.message.text.strip()
    await send(update, t(context, "ask_examples"), kb([[t(context, "skip")]]))
    return EXAMPLES


async def get_examples(update, context):
    txt = update.message.text.strip()
    context.user_data["examples"] = "" if txt == t(context, "skip") else txt
    rows = [[t(context, "deadline_asap"), t(context, "deadline_month")], [t(context, "deadline_2_3"), t(context, "deadline_flex")]]
    await send(update, t(context, "ask_deadline"), kb(rows))
    return DEADLINE


async def get_deadline(update, context):
    context.user_data["deadline"] = update.message.text.strip()
    rows = [[t(context, "contact_tg"), t(context, "skip")], [t(context, "contact_phone"), t(context, "contact_email")]]
    await send(update, t(context, "ask_contact"), kb(rows))
    return CONTACT


async def get_contact(update, context):
    txt = update.message.text.strip()
    if txt == t(context, "skip") or txt == t(context, "contact_tg"):
        context.user_data["contact"] = ""
        return await go_notes(update, context)
    context.user_data["contact_type"] = txt
    await send(update, t(context, "ask_contact_text"), ReplyKeyboardRemove())
    return CONTACT_TEXT


async def get_contact_text(update, context):
    context.user_data["contact"] = update.message.text.strip()
    return await go_notes(update, context)


async def go_notes(update, context):
    rows = [[t(context, "notes_no"), t(context, "notes_yes")]]
    await send(update, t(context, "ask_notes"), kb(rows))
    return NOTES


async def get_notes(update, context):
    txt = update.message.text.strip()
    if txt == t(context, "notes_yes"):
        await send(update, t(context, "ask_notes_text"), ReplyKeyboardRemove())
        return NOTES_TEXT
    context.user_data["notes"] = ""
    return await go_summary(update, context)


async def get_notes_text(update, context):
    context.user_data["notes"] = update.message.text.strip()
    return await go_summary(update, context)


async def go_summary(update, context):
    summary = format_summary(context)
    rows = [[t(context, "confirm_send"), t(context, "restart")]]
    await send(update, t(context, "summary_intro") + "\n\n" + summary, kb(rows))
    return CONFIRM


async def confirm(update, context):
    txt = update.message.text.strip()
    if txt == t(context, "restart"):
        await update.message.reply_text(t(context, "restarted"), reply_markup=ReplyKeyboardRemove())
        return await start(update, context)

    user = update.effective_user
    user_link = '<a href="tg://user?id=' + str(user.id) + '">' + (user.full_name or "Client") + "</a>"
    if user.username:
        user_link += " (@" + user.username + ")"

    header = "🔔 <b>Nova zayavka WebKom</b>\n"
    header += "Klient: " + user_link + "\n"
    header += "💬 <a href=\"tg://user?id=" + str(user.id) + "\">Napsat klientovi</a>\n"
    header += "Cas: " + datetime.now().strftime("%d.%m.%Y %H:%M") + "\n"
    header += "Mova: " + context.user_data.get("lang", "cs").upper() + "\n"
    header += "--------------------\n\n"

    if OWNER_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text=header + format_summary(context),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(str(e))

    await send(update, t(context, "thanks"), ReplyKeyboardRemove())
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
    if d.get("contact"):
        lines.append("<b>" + t(context, "sum_contact") + ":</b> " + d["contact"])
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
            NAME_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_confirm)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            SITE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_site_type)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
            GOAL_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal_text)],
            PAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pages)],
            DESIGN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_design)],
            CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_content)],
            EXAMPLES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_examples)],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_deadline)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            CONTACT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact_text)],
            NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_notes)],
            NOTES_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_notes_text)],
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
