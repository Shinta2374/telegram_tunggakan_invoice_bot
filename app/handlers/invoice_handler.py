from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from app.services.invoice_service import InvoiceService
from app.services.customer_service import CustomerService


invoice_service = InvoiceService()
customer_service = CustomerService()


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

    if value.endswith(".0"):
        try:
            number = float(value)

            if number.is_integer():
                return str(int(number))

        except (
            ValueError,
            TypeError,
        ):
            pass

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

    periode = periode.replace(
        ".0",
        "",
    )

    if len(periode) == 6 and periode.isdigit():

        year = periode[:4]
        month = periode[4:6]

        month_name = MONTH_NAMES.get(
            month
        )

        if month_name:
            return f"{month_name} {year}"

    return periode


def normalize_status(value):
    if value is None:
        return "On Progress"

    status = normalize(value)

    if not status:
        return "On Progress"

    status_lower = status.lower()

    if (
        "sent manual" in status_lower
        or "inv manual" in status_lower
        or "invoice manual" in status_lower
    ):
        return "Invoice manual"

    if (
        "#n/a" in status_lower
        or "no data to display" in status_lower
    ):
        return "On Progress"

    if (
        "message has been sent"
        in status_lower
        or status_lower == "sent"
        or "terkirim" in status_lower
    ):
        return "Terkirim"

    return "On Progress"


def get_customer_name(customer):
    return (
        normalize(customer.get("PELANGGAN"))
        or normalize(customer.get("pelanggan"))
        or normalize(customer.get("nama"))
        or normalize(customer.get("CUSTOMER"))
        or normalize(customer.get("pcTCYC"))
        or normalize(
            customer.get(
                "contr_account_detail"
            )
        )
        or "-"
    )


def get_customer_id(customer):
    fields = (
        "idnumber",
        "customer_id",
        "ID",
        "id",
        "no_jastel",
    )

    for field in fields:

        value = normalize_id(
            customer.get(field)
        )

        if value:
            return value

    return "-"


def get_customer_by_id(customer_id):
    customers = (
        customer_service
        .get_all_customers()
    )

    target_id = normalize_id(
        customer_id
    )

    for customer in customers:

        current_id = get_customer_id(
            customer
        )

        if current_id == target_id:
            return customer

    return None


def get_invoice_period(
    context: ContextTypes.DEFAULT_TYPE,
    invoices=None,
):
    period = context.user_data.get(
        "invoice_period"
    )

    if period:
        return format_periode(
            period
        )

    if invoices:

        first_invoice = invoices[0]

        period = (
            first_invoice.get("periode")
            or first_invoice.get("bill_pe")
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

    text = (
        f"{header}\n\n"
        f"{customer_name} ({customer_id})\n"
    )

    if not invoices:

        text += (
            "\n"
            "Tidak ada invoice yang "
            "tersedia untuk periode ini."
        )

        return text

    text += (
        "\n"
        f"Total Invoice: {len(invoices)}\n"
    )

    for index, invoice in enumerate(
        invoices,
        start=1,
    ):

        billing_amount = format_rupiah(
            invoice.get(
                "billing_amount",
                0,
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
            invoice.get("status")
            or invoice.get("stts")
        )

        text += (
            "\n"
            "────────────────────────────\n\n"
            f"INVOICE {index}\n\n"
            f"Billing Amount  : {billing_amount}\n"
            f"PPN             : {ppn}\n"
            f"Total Amount    : {total_amount}\n"
            f"Status          : {status}\n"
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
        f"[SHOW INVOICE] ID = {customer_id}"
    )

    if not customer_id:

        await query.message.reply_text(
            "ID Pelanggan belum tersedia."
        )

        return

    try:

        customer = get_customer_by_id(
            customer_id
        )

        if customer:

            customer_name = (
                get_customer_name(
                    customer
                )
            )

        else:

            customer_name = "-"

        print(
            "[SHOW INVOICE] "
            f"Customer = {customer_name}"
        )

        invoices = (
            invoice_service
            .get_customer_invoice_data(
                customer_id
            )
        )

        if invoices is None:
            invoices = []

        print(
            "[SHOW INVOICE] "
            f"Jumlah invoice = {len(invoices)}"
        )

        period = get_invoice_period(
            context,
            invoices,
        )

        print(
            "[SHOW INVOICE] "
            f"Periode = {period}"
        )

        text = build_invoice_text(
            customer_id=customer_id,
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

        message = (
            await query.message.reply_text(
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