"""
Handler untuk menampilkan informasi invoice.
"""

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from app.services.invoice_service import (
    InvoiceService,
)


invoice_service = InvoiceService()


def format_rupiah(value):

    try:

        number = float(
            value or 0
        )

        return (
            f"Rp{number:,.0f}"
            .replace(",", ".")
        )

    except (
        ValueError,
        TypeError,
    ):

        return "Rp0"


def normalize_text(value):

    if value is None:
        return "-"

    text = str(value).strip()

    if not text:
        return "-"

    return text


def build_invoice_text(
    customer_id,
    invoices,
):

    if not invoices:

        return (
            "INFORMASI INVOICE\n\n"
            f"ID: `{customer_id}`\n\n"
            "Tidak terdapat invoice "
            "untuk customer ini."
        )

    # Nama pelanggan diambil dari data invoice.
    pelanggan = (
        normalize_text(
            invoices[0].get(
                "pelanggan"
            )
        )
    )

    text = (
        "INFORMASI INVOICE\n\n"
        f"{pelanggan}\n"
        f"ID: `{customer_id}`\n\n"
        f"Total Invoice: {len(invoices)}\n"
    )

    for index, invoice in enumerate(
        invoices,
        start=1,
    ):

        periode = normalize_text(
            invoice.get(
                "periode"
            )
        )

        billing_amount = (
            format_rupiah(
                invoice.get(
                    "billing_amount",
                    0
                )
            )
        )

        ppn = format_rupiah(
            invoice.get(
                "ppn",
                0
            )
        )

        total_amount = (
            format_rupiah(
                invoice.get(
                    "total_amount",
                    0
                )
            )
        )

        status = normalize_text(
            invoice.get(
                "status"
            )
        )

        text += (
            "\n"
            "────────────────────\n\n"
            f"INVOICE {index}\n\n"
            f"Periode        : {periode}\n"
            f"Billing Amount : {billing_amount}\n"
            f"PPN            : {ppn}\n"
            f"Total Amount   : {total_amount}\n"
            f"Status         : {status}\n"
        )

    return text


async def show_invoice(
    query,
    context,
):

    customer_id = (
        context.user_data.get(
            "selected_customer_id"
        )
    )

    print(
        f"[SHOW INVOICE] ID = {customer_id}"
    )

    if not customer_id:

        await query.message.reply_text(
            "ID Pelanggan belum tersedia."
        )

        return

    try:

        invoices = (
            invoice_service
            .get_customer_invoice_data(
                customer_id
            )
        )

        print(
            "[SHOW INVOICE] "
            f"Jumlah invoice = {len(invoices)}"
        )

        text = build_invoice_text(
            customer_id,
            invoices,
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Kembali ke Customer",
                    callback_data=(
                        "close_detail"
                    ),
                )
            ]
        ]

        markup = InlineKeyboardMarkup(
            keyboard
        )

        detail_message_id = (
            context.user_data.get(
                "detail_message_id"
            )
        )

        detail_chat_id = (
            context.user_data.get(
                "detail_chat_id"
            )
        )

        current_chat_id = (
            query.message.chat_id
        )

        # ======================================================
        # EDIT DETAIL YANG SUDAH ADA
        # ======================================================

        if (
            detail_message_id
            and detail_chat_id
            == current_chat_id
        ):

            try:

                await query.get_bot().edit_message_text(
                    chat_id=detail_chat_id,
                    message_id=detail_message_id,
                    text=text,
                    reply_markup=markup,
                    parse_mode="Markdown",
                )

                context.user_data[
                    "detail_type"
                ] = "invoice"

                return

            except Exception as e:

                print(
                    "[INVOICE EDIT ERROR] "
                    f"{e}"
                )

                context.user_data.pop(
                    "detail_message_id",
                    None,
                )

                context.user_data.pop(
                    "detail_chat_id",
                    None,
                )

        # ======================================================
        # DETAIL BELUM ADA
        # ======================================================

        message = (
            await query.message.reply_text(
                text=text,
                reply_markup=markup,
                parse_mode="Markdown",
            )
        )

        context.user_data[
            "detail_message_id"
        ] = message.message_id

        context.user_data[
            "detail_chat_id"
        ] = message.chat_id

        context.user_data[
            "detail_type"
        ] = "invoice"

    except Exception as e:

        print(
            "======================================"
        )

        print(
            "[INVOICE ERROR]"
        )

        print(
            f"Customer ID : {customer_id}"
        )

        print(
            f"Error Type  : {type(e).__name__}"
        )

        print(
            f"Error       : {e}"
        )

        print(
            "======================================"
        )

        await query.message.reply_text(
            "Terjadi kesalahan saat "
            "mengambil data invoice."
        )