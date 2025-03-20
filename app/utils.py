import json
import logging
import os
import re
from telegram import Update

logger = logging.getLogger(__name__)

domain_by_chat_id = {
    int(chat_id): domain
    for entry in os.environ["DOMAIN_BY_CHAT_ID"].split(",")
    for chat_id, domain in [entry.split(":")]
}

aliases_by_domain = {
    parts[0]: parts[1].split("|") if len(parts) > 1 else []
    for group in os.environ.get("ALIASES_BY_DOMAIN", "").split(",")
    if group
    for parts in [group.split(":")]
}


def get_domain_from_chat(update: Update) -> str:
    chat_id = update.message.chat_id
    if chat_id not in domain_by_chat_id:
        logger.error(f"Chat ID {chat_id} not set up")
        raise ValueError(f"Chat ID {chat_id} not set up")
    return domain_by_chat_id[chat_id]


def get_shortcode(update: Update) -> str:
    domain = get_domain_from_chat(update)
    shortcode = update.message.text

    if shortcode.startswith(f"https://{domain}/"):
        shortcode = shortcode[len(f"https://{domain}/") :]
    elif re.match(r"^https?://", shortcode):
        raise ValueError(f"When using a full url, it should be in the {domain} domain.")
    if not re.match(r"^[a-zA-Z0-9_-]+$", shortcode):
        raise ValueError(
            "Shortcode must only contain letters, numbers, hyphens, and underscores."
        )

    return shortcode if shortcode else "_default_"


def get_full_state() -> dict:
    file_path = os.environ["CONFIG_PATH"]
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    return data


def get_domain_state(domain: str) -> dict:
    return get_full_state().get(domain, {})


def save_domain_state(domain: str, domain_data: dict) -> None:
    data = get_full_state()
    data[domain] = domain_data

    file_path = os.environ["CONFIG_PATH"]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    update_nginx_file(domain)


def write_nginx_conf(domain: str, domain_data: dict, default: str = "") -> None:
    redirects = "\n".join(
        (
            f"""    location ~* ^/{get_path_for_shortcode(shortcode)}$ {{
        return 302 "{url}";
    }}"""
            for shortcode, url in domain_data.items()
        )
    )
    browser_redirects = "\n".join(f'        if ($arg_q ~* "^((%20)|\+|(%2C))*{shortcode}((%20)|\+|(%2C))*$") {{ return 302 "{url}"; }}' for shortcode, url in domain_data.items() if shortcode)
    default = default or 'default_type text/plain;return 404 "Invalid url.\\n";'
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

    if ($http_user_agent ~* "Slackbot-LinkExpanding") {{
        return 403;
    }}

{redirects}

    location = /browser {{
{browser_redirects}
        return 302 "https://kagi.com/search?q=$arg_q";
    }}

    location / {{
        access_log off;
        {default}
    }}
}}
"""
        )


def update_nginx_file(domain: str) -> None:
    data = get_full_state()
    domain_data = data.get(domain, {})

    write_nginx_conf(domain, domain_data)


def update_nginx_files() -> None:
    for domain in domain_by_chat_id.values():
        update_nginx_file(domain)


def get_path_for_shortcode(shortcode: str) -> str:
    return "" if shortcode == "_default_" else f"{shortcode}"


async def reply_message(update: Update, text: str) -> None:
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        do_quote=False,
        disable_web_page_preview=True,
    )
