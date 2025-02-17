import logging
import os
import os.path
from conversations import add_shortcode, del_shortcode, list_shortcodes
from telegram import Update
from telegram.ext import (
    Application,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main() -> None:
    application = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    application.add_handler(add_shortcode.handler)
    application.add_handler(del_shortcode.handler)
    application.add_handler(list_shortcodes.handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
