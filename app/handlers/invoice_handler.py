from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from app.services.invoice_service import InvoiceService


invoice_service = InvoiceService()


MONTH_NAMES = {
    "01": "Januari",
    "02": "Februari",
    "03": "Maret",
    "04": "April",
    "05": "Mei",
    "06": "Juni",
    "07": "Juli",
    "08": "Agustus",
    "09": "September",
    "10": "Oktober",
    "11": "November",
    "12": "Desember",
}


def normalize(value):
    if value is None:
        return ""

    return str(value).strip()


def normalize_id(value):
    value = normalize(value)

    if not value:
        return ""

    try:
        number = float(value)

        if number.is_integer():
            return str(int(number))

    except (
        ValueError,
        TypeError,
    ):
        pass

    return value


def normalize_text(value):
    value = normalize(value)

    if not value:
        return "-"

    return value


def format_rupiah(value):
    try:
        number = float(value or 0)

        return (
            f"Rp{number:,.0f}"
            .replace(",", ".")
        )

    except (
        ValueError,
        TypeError,
    ):
        return "Rp0"


def format_periode(value):
    periode = normalize(value)

    if not periode:
        return "-"

    try:
        number = float(periode)

        if number.is_integer():
            periode = str(int(number))

    except (
        ValueError,
        TypeError,
    ):
        pass

    if (
        len(periode) == 6
        and periode.isdigit()
    ):
        year = periode[:4]
        month = periode[4:6]

        month_name = MONTH_NAMES.get(
            month
        )

        if month_name:
            return (
                f"{month_name} "
                f"{year}"
            )

    return periode


def normalize_status(value):
    if value is None:
        return "On Progress"

    status = normalize(value)

    if not status:
        return "On Progress"

    status_lower = status.lower()

    if (
        "no data to display"
        in status_lower
        or "#n/a" in status_lower
        or status_lower == "n/a"
    ):
        return "On Progress"

    manual_keywords = [
        "inv manual",
        "invoice manual",
        "sent tghn manual",
        "sent manual",
        "manual via ideas",
        "klik sent manual",
    ]

    for keyword in manual_keywords:
        if keyword in status_lower:
            return "Invoice Manual"

    if (
        "message has been sent"
        in status_lower
        or status_lower == "sent"
        or "terkirim" in status_lower
    ):
        return "Terkirim"

    return normalize_text(value)


def get_invoice_customer(customer_id):
    target_id = normalize_id(
        customer_id
    )

    if not target_id:
        return None

    return (
        invoice_service
        .get_invoice_customer(
            target_id
        )
    )


def get_invoice_period(
    context,
    invoices=None,
):
    period = (
        context.user_data.get(
            "invoice_period"
        )
    )

    if period:
        return format_periode(
            period
        )

    try:
        period = (
            invoice_service
            .get_invoice_period()
        )

        if period:
            return format_periode(
                period
            )

    except Exception as error:
        print(
            "[INVOICE PERIOD ERROR] "
            f"{error}"
        )

    if invoices:
        first_invoice = invoices[0]

        period = (
            first_invoice.get(
                "periode"
            )
            or first_invoice.get(
                "bill_pe"
            )
        )

        if period:
            return format_periode(
                period
            )

    return "-"


def build_invoice_text(
    customer_id,
    customer_name,
    invoices,
    period,
):
    if period != "-":
        header = (
            "INFORMASI INVOICE BULAN "
            f"{period.upper()}"
        )

    else:
        header = (
            "INFORMASI INVOICE BULAN"
        )

    customer_name = normalize_text(
        customer_name
    )

    customer_id = normalize_id(
        customer_id
    )

    text = (
        f"{header}\n\n"
        f"{customer_name} "
        f"({customer_id})\n"
    )

    if not invoices:
        text += (
            "\nTidak ada invoice yang "
            "tersedia untuk periode ini."
        )

        return text

    text += (
        f"\nTotal Invoice: "
        f"{len(invoices)}\n"
    )

    for index, invoice in enumerate(
        invoices,
        start=1,
    ):
        billing_amount = (
            format_rupiah(
                invoice.get(
                    "billing_amount",
                    0,
                )
            )
        )

        ppn = format_rupiah(
            invoice.get(
                "ppn",
                0,
            )
        )

        total_amount = format_rupiah(
            invoice.get(
                "total_amount",
                0,
            )
        )

        status = normalize_status(
            invoice.get(
                "status"
            )
            or invoice.get(
                "stts"
            )
        )

        text += (
            "\n──────────────────────────\n\n"
            f"INVOICE {index}\n\n"
            f"Billing Amount  : "
            f"{billing_amount}\n"
            f"PPN             : "
            f"{ppn}\n"
            f"Total Amount    : "
            f"{total_amount}\n"
            f"Status          : "
            f"{status}\n"
        )

    return text


async def show_invoice(
    query,
    context: ContextTypes.DEFAULT_TYPE,
):
    customer_id = (
        context.user_data.get(
            "selected_customer_id"
        )
    )

    print(
        f"[SHOW INVOICE] "
        f"ID = {customer_id}"
    )

    if not customer_id:
        try:
            await query.edit_message_text(
                "ID Pelanggan belum tersedia."
            )

        except Exception as error:
            print(
                "[INVOICE ERROR] "
                f"{error}"
            )

        return

    try:
        normalized_customer_id = (
            normalize_id(
                customer_id
            )
        )

        invoice_customer = (
            get_invoice_customer(
                normalized_customer_id
            )
        )

        if invoice_customer:
            customer_name = (
                invoice_customer.get(
                    "pelanggan"
                )
                or invoice_customer.get(
                    "customer_name"
                )
                or "-"
            )

        else:
            customer_name = "-"

        invoices = (
            invoice_service
            .get_customer_invoice_data(
                normalized_customer_id
            )
        )

        if invoices is None:
            invoices = []

        period = get_invoice_period(
            context,
            invoices,
        )

        text = build_invoice_text(
            customer_id=(
                normalized_customer_id
            ),
            customer_name=customer_name,
            invoices=invoices,
            period=period,
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Kembali",
                    callback_data=(
                        "back_to_customer_list"
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
                )

                print(
                    "[INVOICE] "
                    "Detail ditampilkan "
                    "pada pesan yang sama."
                )

            except Exception as error:
                if (
                    "Message is not modified"
                    not in str(error)
                ):
                    print(
                        "[INVOICE EDIT ERROR] "
                        f"{error}"
                    )

                    message = (
                        await query.get_bot()
                        .send_message(
                            chat_id=current_chat_id,
                            text=text,
                            reply_markup=markup,
                        )
                    )

                    context.user_data[
                        "detail_message_id"
                    ] = message.message_id

                    context.user_data[
                        "detail_chat_id"
                    ] = message.chat_id

        else:
            message = (
                await query.get_bot()
                .send_message(
                    chat_id=current_chat_id,
                    text=text,
                    reply_markup=markup,
                )
            )

            context.user_data[
                "detail_message_id"
            ] = message.message_id

            context.user_data[
                "detail_chat_id"
            ] = message.chat_id

            print(
                "[INVOICE] "
                "Detail dikirim sebagai "
                "pesan baru."
            )

        context.user_data[
            "detail_type"
        ] = "invoice"

    except Exception as error:
        print(
            "======================================"
        )

        print(
            "[INVOICE ERROR]"
        )

        print(
            f"Customer ID : "
            f"{customer_id}"
        )

        print(
            f"Error Type  : "
            f"{type(error).__name__}"
        )

        print(
            f"Error       : "
            f"{error}"
        )

        print(
            "======================================"
        )

        error_text = (
            "❌ GAGAL MEMPROSES "
            "DATA INVOICE\n\n"
            "Terjadi kesalahan saat "
            "mengambil data invoice.\n\n"
            "Silakan coba lagi."
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Kembali",
                    callback_data=(
                        "back_to_customer_list"
                    ),
                )
            ]
        ]

        markup = InlineKeyboardMarkup(
            keyboard
        )

        try:
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

            if (
                detail_message_id
                and detail_chat_id
                == current_chat_id
            ):
                await query.get_bot().edit_message_text(
                    chat_id=detail_chat_id,
                    message_id=detail_message_id,
                    text=error_text,
                    reply_markup=markup,
                )

            else:
                await query.message.reply_text(
                    error_text,
                    reply_markup=markup,
                )

        except Exception as fallback_error:
            print(
                "[INVOICE FALLBACK ERROR] "
                f"{fallback_error}"
            )