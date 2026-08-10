"""
Handler /start
"""

from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(

        "👋 Selamat datang di Telkom Customer Service\n\n"

        "Silakan masukkan ID Pelanggan Anda."

    )