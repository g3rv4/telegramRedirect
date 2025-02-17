import logging
import os
import os.path
from conversations import add_shortcode, del_shortcode
from commands import list_shortcodes, update_nginx
from telegram import Update
from telegram.ext import Application,CommandHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main() -> None:
    application = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    application.add_handler(add_shortcode.handler)
    application.add_handler(del_shortcode.handler)
    application.add_handler(CommandHandler("list", list_shortcodes.handle))
    application.add_handler(CommandHandler("update_nginx", update_nginx.handle))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
