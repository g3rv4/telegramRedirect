import json
import logging
import os
import os.path
import re

from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

domain_by_chat_id = {
    int(chat_id): domain
    for entry in os.environ["DOMAIN_BY_CHAT_ID"].split(",")
    for chat_id, domain in [entry.split(":")]
}
aliases_by_domain = {
        parts[0]: parts[1].split('|') if len(parts) > 1 else []
        for group in os.environ.get("ALIASES_BY_DOMAIN", "").split(',') if group
        for parts in [group.split(':')]
    }


def get_path_for_shortcode(shortcode: str) -> str:
    return "" if shortcode == "_default_" else f"{shortcode}"


async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    domain = domain_by_chat_id.get(update.message.chat_id)
    if not domain:
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="The bot is not configured to use this chat.",
        )
        return

    file_path = os.environ["CONFIG_PATH"]
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    if domain not in data:
        data[domain] = {}
    domain_data = data[domain]

    parts = update.message.text.split(" ")
    msg = None
    if len(parts) == 1:
        shortcode = parts[0]
        if shortcode not in domain_data:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text=f"Redirect `{shortcode}` not found.",
                parse_mode="Markdown",
            )
            return

        msg = f"Redirect `{shortcode}` to `{domain_data[shortcode]}` deleted."
        del domain_data[shortcode]
    elif len(parts) == 2:
        shortcode, url = parts

        if not re.match(r"^[a-zA-Z0-9_-]+$", shortcode):
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Shortcode must only contain letters, numbers, hyphens, and underscores.",
            )
            return

        if not re.match(r"^https?://", url):
            url = f"https://{url}"

        if shortcode in domain_data:
            msg = f"Redirect `{shortcode}` updated from `{domain_data[shortcode]}` to `{url}`."
        else:
            msg = f"Redirect `{shortcode}` to `{url}` added."
        msg += f"\n\n```https://{domain}/{get_path_for_shortcode(shortcode)}```"

        domain_data[shortcode] = url
    else:
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Either enter `shortcode url` to add or update a redirect or `shortcode` to delete it.",
        )
        return

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    if not os.path.exists(os.environ["NGINX_CONFIG_PATH"]):
        os.makedirs(os.environ["NGINX_CONFIG_PATH"])

    redirects = "\n".join(
        (
            f"""    location = /{get_path_for_shortcode(shortcode)} {{
        return 302 {url};
    }}"""
            for shortcode, url in domain_data.items()
        )
    )
    with open(
        os.path.join(os.environ["NGINX_CONFIG_PATH"], domain + ".conf"),
        "w",
        encoding="utf-8",
    ) as f:
        f.write(
            f"""
server {{
    listen 80;
    server_name {domain} {" ".join(aliases_by_domain.get(domain, []))};

{redirects}

    location / {{
        default_type text/plain;
        return 404 "Invalid url.\n";
    }}
}}
"""
        )

    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=msg,
        parse_mode="Markdown",
    )


def main() -> None:
    application = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, process_message)
    )
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
