"""
Konfigurasi utama Telegram Bot.
"""

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
from app.handlers.command_handler import command_handler


class TelegramBot:

    def __init__(self):

        self.application = (
            Application.builder()
            .token(settings.BOT_TOKEN)
            .build()
        )

        self.register_handlers()

    def register_handlers(self):

        # ==================================================
        # /START
        # ==================================================

        self.application.add_handler(
            CommandHandler(
                "start",
                start,
            )
        )

        # ==================================================
        # COMMAND
        # ==================================================

        self.application.add_handler(
            CommandHandler(
                [
                    "tgkn",
                    "inv",
                    "cyc",
                    "am",
                    "cust",
                    "help",
                ],
                command_handler,
            )
        )

        # ==================================================
        # CALLBACK
        # ==================================================

        self.application.add_handler(
            CallbackQueryHandler(
                callback_handler,
            )
        )

        # ==================================================
        # TEXT MESSAGE
        # ==================================================

        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_message,
            )
        )

    def run(self):

        print()
        print("Telegram Bot Running...")
        print()
        print(
            "Registered commands: "
            "/start /tgkn /inv /cyc /am /cust /help"
        )
        print()

        self.application.run_polling()