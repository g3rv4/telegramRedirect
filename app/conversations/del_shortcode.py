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
)

SHORTCODE = range(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        domain = get_domain_from_chat(update)
    except ValueError:
        await reply_message(update, "This chat is not set up to use the bot.")
        return ConversationHandler.END

    await reply_message(
        update,
        f"Please type the shortcode or the {domain} url to delete (use /stop to cancel)",
    )

    return SHORTCODE


async def shortcode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        shortcode = get_shortcode(update)
    except ValueError as e:
        await reply_message(update, f"{e} Try again with a valid shortcode.")
        return SHORTCODE

    domain = get_domain_from_chat(update)
    domain_data = get_domain_state(domain)
    if shortcode not in domain_data:
        await reply_message(update, f"Shortcode `{shortcode}` not found.")
        return ConversationHandler.END
    
    del domain_data[shortcode]
    save_domain_state(domain, domain_data)
    await reply_message(update, f"Shortcode `{shortcode}` deleted.")

    return ConversationHandler.END


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Done!", do_quote=False)
    return ConversationHandler.END


handler = ConversationHandler(
    entry_points=[CommandHandler("del", start)],
    states={
        SHORTCODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, shortcode)],
    },
    fallbacks=[CommandHandler("stop", stop)],
)
