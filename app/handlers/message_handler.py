"""
Handler untuk pesan teks biasa.
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.customer_handler import (
    show_ams,
    search_customers,
)

from app.services.customer_service import (
    CustomerService,
)


customer_service = CustomerService()


def normalize(value):

    if value is None:
        return ""

    return str(value).strip()


def get_customer_am(customer):

    return (
        normalize(customer.get("AM"))
        or normalize(customer.get("am"))
    )


async def receive_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Menangani input teks berdasarkan search_mode.
    """

    if not update.message:
        return

    text = normalize(
        update.message.text
    )

    if not text:
        return

    search_mode = context.user_data.get(
        "search_mode"
    )

    # ========================================================
    # SEARCH AM
    # ========================================================

    if search_mode == "am":

        customers = (
            customer_service.get_all_customers()
        )

        keyword = text.lower()

        am_names = set()

        for customer in customers:

            am = get_customer_am(
                customer
            )

            if not am:
                continue

            if keyword in am.lower():

                am_names.add(
                    am
                )

        context.user_data[
            "search_mode"
        ] = None

        if not am_names:

            await update.message.reply_text(
                "❌ AM tidak ditemukan.\n\n"
                f"Pencarian: {text}"
            )

            return

        await show_ams(
            update,
            context,
            page=0,
            search_results=sorted(
                am_names
            )
        )

        return

    # ========================================================
    # SEARCH CUSTOMER
    # ========================================================

    if search_mode == "customer":

        context.user_data[
            "search_mode"
        ] = None

        await search_customers(
            update,
            context,
            text
        )

        return

    # ========================================================
    # INPUT BIASA
    # ========================================================

    await update.message.reply_text(
        "Silakan gunakan menu yang tersedia.\n\n"
        "Ketik /start untuk kembali."
    )