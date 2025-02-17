import re
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from utils import (
    get_domain_from_chat,
    reply_message,
    get_domain_state,
    get_shortcode,
    save_domain_state,
    get_path_for_shortcode,
)

SHORTCODE, TARGET_URL = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        get_domain_from_chat(update)
    except ValueError:
        await reply_message(update, "This chat is not set up to use the bot.")
        return ConversationHandler.END

    await reply_message(
        update,
        "Please type the shortcode to add (use /stop to cancel)",
    )

    return SHORTCODE


async def shortcode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        shortcode = get_shortcode(update)
        context.user_data["shortcode"] = shortcode
    except ValueError as e:
        await reply_message(update, f"{e} Try again with a valid shortcode.")
        return SHORTCODE

    domain_data = get_domain_state(get_domain_from_chat(update))
    current_state = (
        f" (current target: `{domain_data[shortcode]}`)"
        if shortcode in domain_data
        else ""
    )

    await reply_message(
        update,
        f"Adding shortcode: `{shortcode}`{current_state}. What is the target URL? (use /stop to cancel)",
    )

    return TARGET_URL


async def target_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    shortcode = context.user_data["shortcode"]

    target_url = update.message.text
    if not re.match(r"^https?://", target_url):
        target_url = f"https://{target_url}"

    domain = get_domain_from_chat(update)
    domain_data = get_domain_state(domain)
    domain_data[shortcode] = target_url
    save_domain_state(domain, domain_data)

    full_url = f"https://{domain}/{get_path_for_shortcode(shortcode)}"
    await reply_message(update, f"Done! {full_url} is set up.")

    return ConversationHandler.END


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Done!", do_quote=False)
    return ConversationHandler.END


handler = ConversationHandler(
    entry_points=[CommandHandler("add", start)],
    states={
        SHORTCODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, shortcode)],
        TARGET_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, target_url)],
    },
    fallbacks=[CommandHandler("stop", stop)],
)
