from telegram import Update
from telegram.ext import ContextTypes
from utils import get_domain_from_chat, update_nginx_files, reply_message


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        get_domain_from_chat(update)
    except ValueError:
        await reply_message(update, "This chat is not set up to use the bot.")
        return

    update_nginx_files()
    await reply_message(update, "Nginx configuration updated.")
