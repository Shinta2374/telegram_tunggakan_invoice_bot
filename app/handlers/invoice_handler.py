from telegram import CallbackQuery
from telegram.ext import ContextTypes

from app.services.invoice_service import InvoiceService
from app.keyboards.back_menu import get_back_menu

service = InvoiceService()


async def show_invoice(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE
):

    result = service.get_invoice()

    await query.message.reply_text(

        result,

        reply_markup=get_back_menu()

    )