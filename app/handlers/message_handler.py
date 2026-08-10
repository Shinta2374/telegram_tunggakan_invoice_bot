"""
Handler menerima ID pelanggan
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.services.customer_service import CustomerService
from app.keyboards.main_menu import get_main_menu


customer_service = CustomerService()


async def receive_message(update: Update,
                          context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    customer = customer_service.find_by_id(text)

    if customer is None:

        await update.message.reply_text(

            "❌ ID Pelanggan tidak ditemukan.\n\n"

            "Silakan masukkan kembali."

        )

        return

    context.user_data["idnumber"] = customer["idnumber"]

    context.user_data["nama"] = customer["NAMA"]

    await update.message.reply_text(

        f"Halo, {customer['NAMA']}\n\n"

        "Silakan pilih layanan.",

        reply_markup=get_main_menu()

    )