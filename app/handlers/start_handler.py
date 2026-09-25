"""
Handler command /start.
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.customer_handler import (
    show_ams
)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # ==========================================
    # RESET STATE
    # ==========================================

    context.user_data.clear()

    # ==========================================
    # WELCOME
    # ==========================================

    if update.message:

        await update.message.reply_text(
            "Selamat datang di "
            "NETA Chatbot Services."
        )

        await show_ams(
            update,
            context,
            page=0
        )