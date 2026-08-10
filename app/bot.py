from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from app.config.settings import settings

from app.handlers.start_handler import start
from app.handlers.message_handler import receive_message
from app.handlers.callback_handler import callback_handler


class TelegramBot:

    def __init__(self):

        self.application = (
            Application.builder()
            .token(settings.BOT_TOKEN)
            .build()
        )

        self.register_handlers()

    def register_handlers(self):

        self.application.add_handler(

            CommandHandler(
                "start",
                start
            )

        )

        self.application.add_handler(

            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_message
            )

        )

        self.application.add_handler(

            CallbackQueryHandler(
                callback_handler
            )

        )

    def run(self):

        print("=" * 50)
        print("Telegram Bot Running...")
        print("=" * 50)

        self.application.run_polling()