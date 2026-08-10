"""
Handler Informasi Tunggakan
"""

from telegram import CallbackQuery
from telegram.ext import ContextTypes

from app.services.tunggakan_service import TunggakanService
from app.formatters.tunggakan_formatter import TunggakanFormatter
from app.keyboards.back_menu import get_back_menu


service = TunggakanService()


async def show_tunggakan(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE
):

    idnumber = context.user_data["idnumber"]

    result = service.get_tunggakan(idnumber)

    message = TunggakanFormatter.format(result)

    await query.message.reply_text(

        text=message,

        parse_mode="HTML",

        reply_markup=get_back_menu()

    )