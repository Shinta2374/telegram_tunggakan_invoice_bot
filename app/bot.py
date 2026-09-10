from telegram import (
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from app.config.settings import settings
from app.services.auth_service import AuthService

from app.handlers.auth_handler import auth_start_handler
from app.handlers.message_handler import receive_message
from app.handlers.callback_handler import callback_handler
from app.handlers.command_handler import command_handler


async def setup_commands(application):
    user_commands = [
        BotCommand("start", "Membuka Menu Utama"),
        BotCommand("tgkn", "Menampilkan Tunggakan"),
        BotCommand("inv", "Menampilkan Invoice"),
        BotCommand(
            "cyc",
            "Menampilkan Pelanggan dengan Tunggakan",
        ),
        BotCommand("am", "Daftar AM"),
        BotCommand("cust", "Cari Customer"),
        BotCommand("help", "Menampilkan Panduan"),
    ]

    admin_commands = user_commands + [
        BotCommand(
            "acc",
            "Cek request user baru",
        ),
    ]

    await application.bot.set_my_commands(
        user_commands,
        scope=BotCommandScopeDefault(),
    )

    for admin_id in settings.ADMIN_IDS:
        try:
            await application.bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(
                    chat_id=admin_id,
                ),
            )

            print(
                f"[COMMAND] Admin menu registered "
                f"for {admin_id}"
            )

        except Exception as error:
            print(
                f"[COMMAND ERROR] Failed to register "
                f"admin menu for {admin_id}: {error}"
            )


class TelegramBot:

    def __init__(self):
        self.application = (
            Application.builder()
            .token(settings.BOT_TOKEN)
            .post_init(setup_commands)
            .build()
        )

        self.initialize_database()
        self.register_handlers()

    def initialize_database(self):
        auth_service = AuthService()
        auth_service.initialize()

        print(
            "Database initialization berhasil."
        )

    def register_handlers(self):

        self.application.add_handler(
            CommandHandler(
                "start",
                auth_start_handler,
            )
        )

        self.application.add_handler(
            CommandHandler(
                [
                    "tgkn",
                    "inv",
                    "cyc",
                    "am",
                    "cust",
                    "help",
                    "acc",
                ],
                command_handler,
            )
        )

        self.application.add_handler(
            CallbackQueryHandler(
                callback_handler,
            )
        )

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
            "/start /tgkn /inv /cyc /am /cust /help /acc"
        )

        print()

        self.application.run_polling()