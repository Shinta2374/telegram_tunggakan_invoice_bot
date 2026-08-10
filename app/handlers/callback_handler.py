from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.tunggakan_handler import show_tunggakan
from app.handlers.invoice_handler import show_invoice
from app.keyboards.main_menu import get_main_menu


async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.data == "tunggakan":

        await show_tunggakan(query, context)

    elif query.data == "invoice":

        await show_invoice(query, context)

    elif query.data == "back_menu":

        await query.message.reply_text(

            "Silakan pilih layanan.",

            reply_markup=get_main_menu()

        )

    elif query.data == "change_id":

        context.user_data.clear()

        await query.message.reply_text(

            "Silakan masukkan ID Pelanggan yang baru."

        )