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
from app.services.invoice_service import InvoiceService

from app.handlers.auth_handler import auth_start_handler
from app.handlers.message_handler import receive_message
from app.handlers.callback_handler import callback_handler
from app.handlers.command_handler import command_handler


async def setup_commands(application):
    user_commands = [
        BotCommand(
            "start",
            "Membuka Menu Utama",
        ),
        BotCommand(
            "inv",
            "Menampilkan Invoice",
        ),
        BotCommand(
            "cyc",
            "Menampilkan Saldo CYC",
        ),
        BotCommand(
            "cr",
            "Menampilkan Saldo CR",
        ),
        BotCommand(
            "am",
            "Daftar AM",
        ),
        BotCommand(
            "help",
            "Menampilkan Panduan",
        ),
    ]

    admin_commands = user_commands + [
        BotCommand(
            "acc",
            "Cek request user baru",
        ),
    ]

    # Command untuk user biasa
    await application.bot.set_my_commands(
        user_commands,
        scope=BotCommandScopeDefault(),
    )

    # Command tambahan khusus admin
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
        self.initialize_invoice_cache()
        self.register_handlers()

    def initialize_database(self):
        auth_service = AuthService()
        auth_service.initialize()

        print(
            "Database initialization berhasil."
        )

    def initialize_invoice_cache(self):
        try:
            invoice_service = InvoiceService()

            print(
                "[INVOICE CACHE] Memulai preload invoice..."
            )

            invoice_customers = (
                invoice_service.get_invoice_customers()
            )

            print(
                "[INVOICE CACHE] Preload berhasil. "
                f"{len(invoice_customers)} customer invoice."
            )

        except Exception as error:
            print(
                "[INVOICE CACHE ERROR] "
                f"Gagal melakukan preload: {error}"
            )

    def register_handlers(self):

        # /start
        self.application.add_handler(
            CommandHandler(
                "start",
                auth_start_handler,
            )
        )

        # Command utama
        self.application.add_handler(
            CommandHandler(
                [
                    "inv",
                    "cyc",
                    "cr",
                    "am",
                    "help",
                    "acc",
                ],
                command_handler,
            )
        )

        # Callback dari inline keyboard
        self.application.add_handler(
            CallbackQueryHandler(
                callback_handler,
            )
        )

        # Pesan teks biasa
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
            "/start /inv /cyc /cr /am /help /acc"
        )

        print()

        self.application.run_polling()