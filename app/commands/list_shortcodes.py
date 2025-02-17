from telegram import Update
from telegram.ext import ContextTypes
from utils import (
    get_domain_from_chat,
    reply_message,
    get_domain_state,
    get_path_for_shortcode,
)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        domain = get_domain_from_chat(update)
    except ValueError:
        await reply_message(update, "This chat is not set up to use the bot.")
        return

    domain_data = get_domain_state(domain)
    if not domain_data:
        await reply_message(update, "No redirects configured.")
    else:
        items = sorted(domain_data.items())
        for i in range(0, len(items), 20):
            chunk = items[i : i + 20]
            await reply_message(
                update,
                "\n".join(
                    f"• [{shortcode}](https://{domain}/{get_path_for_shortcode(shortcode)}) -> `{url}`"
                    for shortcode, url in chunk
                ),
            )
