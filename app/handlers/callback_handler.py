from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes

from app.handlers.customer_handler import (
    show_ams,
    show_customers,
)

from app.handlers.tunggakan_handler import (
    show_tunggakan,
)

from app.services.invoice_service import (
    InvoiceService,
)


invoice_service = InvoiceService()


async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = query.data

    print(
        f"[CALLBACK] {data}"
    )

    if data == "noop":
        return

    # Pilih AM
    if data.startswith("select_am:"):

        am_name = data.split(
            ":",
            1,
        )[1].strip()

        print(
            f"[AM DIPILIH] {am_name}"
        )

        context.user_data[
            "current_am"
        ] = am_name

        context.user_data[
            "customer_page"
        ] = 0

        context.user_data[
            "selected_customer_id"
        ] = None

        clear_detail_state(
            context
        )

        await show_customers(
            update,
            context,
            page=0,
        )

        return

    # Pagination AM
    if data.startswith("am_page:"):

        try:

            page = int(
                data.split(
                    ":",
                    1,
                )[1]
            )

        except (
            ValueError,
            IndexError,
        ):

            print(
                f"[CALLBACK ERROR] "
                f"Invalid AM page: {data}"
            )

            return

        await show_ams(
            update,
            context,
            page=page,
        )

        return

    # Kembali ke AM
    if data == "back_to_ams":

        context.user_data[
            "current_am"
        ] = None

        context.user_data[
            "customer_page"
        ] = 0

        context.user_data[
            "selected_customer_id"
        ] = None

        clear_detail_state(
            context
        )

        await show_ams(
            update,
            context,
            page=0,
        )

        return

    # Pagination customer
    if data.startswith("customer_page:"):

        try:

            page = int(
                data.split(
                    ":",
                    1,
                )[1]
            )

        except (
            ValueError,
            IndexError,
        ):

            print(
                f"[CALLBACK ERROR] "
                f"Invalid customer page: {data}"
            )

            return

        context.user_data[
            "customer_page"
        ] = page

        context.user_data[
            "selected_customer_id"
        ] = None

        clear_detail_state(
            context
        )

        await show_customers(
            update,
            context,
            page=page,
        )

        return

    # Search AM
    if data == "search_am":

        context.user_data[
            "search_mode"
        ] = "am"

        await query.message.reply_text(
            "Silakan masukkan nama AM "
            "yang ingin dicari."
        )

        return

    # Search customer
    if data == "search_customer":

        context.user_data[
            "search_mode"
        ] = "customer"

        await query.message.reply_text(
            "Silakan masukkan nama perusahaan "
            "atau ID pelanggan."
        )

        return

    # Tunggakan
    if data.startswith("tunggakan:"):

        customer_id = data.split(
            ":",
            1,
        )[1].strip()

        print(
            f"[TUNGGAKAN] ID = {customer_id}"
        )

        context.user_data[
            "selected_customer_id"
        ] = customer_id

        await show_tunggakan(
            query,
            context,
        )

        return

    # Invoice
    if data.startswith("invoice:"):

        customer_id = data.split(
            ":",
            1,
        )[1].strip()

        print(
            f"[INVOICE] ID = {customer_id}"
        )

        context.user_data[
            "selected_customer_id"
        ] = customer_id

        await show_invoice(
            query,
            context,
        )

        return

    # Kembali ke customer
    if data in (
        "back_to_customers",
        "close_detail",
    ):

        page = context.user_data.get(
            "customer_page",
            0,
        )

        print(
            f"[CLOSE DETAIL] "
            f"Customer page = {page}"
        )

        context.user_data[
            "selected_customer_id"
        ] = None

        clear_detail_state(
            context
        )

        await show_customers(
            update,
            context,
            page=page,
        )

        return

    print(
        f"[WARNING] Callback tidak dikenal: {data}"
    )


def clear_detail_state(
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.pop(
        "detail_message_id",
        None,
    )

    context.user_data.pop(
        "detail_chat_id",
        None,
    )

    context.user_data.pop(
        "detail_type",
        None,
    )


def format_rupiah(
    value,
):

    try:

        number = float(
            value or 0
        )

        return (
            f"Rp{number:,.0f}"
            .replace(
                ",",
                ".",
            )
        )

    except (
        ValueError,
        TypeError,
    ):

        return "Rp0"


def normalize_invoice_status(
    status,
):

    if status is None:
        return "Belum Terkirim"

    status = str(
        status
    ).strip()

    if not status:
        return "Belum Terkirim"

    normalized = status.lower()

    if (
        "no data to display"
        in normalized
    ):

        return "Belum Terkirim"

    if normalized in (
        "#n/a",
        "n/a",
    ):

        return "On Progress"

    if "manual" in normalized:

        return "Invoice Manual"

    return status


def build_invoice_text(
    invoices,
):

    if not invoices:

        return (
            "<b>INFORMASI INVOICE</b>\n\n"
            "Tidak terdapat data invoice "
            "untuk customer ini."
        )

    first = invoices[0]

    customer_id = (
        first.get(
            "customer_id"
        )
        or first.get(
            "no_jastel"
        )
        or "-"
    )

    customer_name = (
        first.get(
            "pelanggan"
        )
        or first.get(
            "contr_account_detail"
        )
        or "-"
    )

    text = (
        "<b>INFORMASI INVOICE</b>\n\n"
        f"<b>Customer</b>\n"
        f"{customer_name}\n\n"
        f"<b>ID Pelanggan</b>\n"
        f"<code>{customer_id}</code>\n\n"
        f"<b>Total Invoice:</b> "
        f"{len(invoices)}"
    )

    for index, invoice in enumerate(
        invoices,
        start=1,
    ):

        periode = (
            invoice.get(
                "periode"
            )
            or invoice.get(
                "bill_pe"
            )
            or "-"
        )

        billing_amount = invoice.get(
            "billing_amount",
            0,
        )

        ppn = invoice.get(
            "ppn",
            0,
        )

        total_amount = invoice.get(
            "total_amount",
            0,
        )

        raw_status = (
            invoice.get(
                "status"
            )
            or invoice.get(
                "stts"
            )
        )

        status = normalize_invoice_status(
            raw_status
        )

        text += (
            "\n\n"
            "────────────────────\n"
            f"<b>Invoice {index}</b>\n\n"
            f"Periode: {periode}\n"
            f"Billing Amount: "
            f"{format_rupiah(billing_amount)}\n"
            f"PPN: "
            f"{format_rupiah(ppn)}\n"
            f"Total Amount: "
            f"{format_rupiah(total_amount)}\n"
            f"Status: <b>{status}</b>"
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

        if not invoice_service.file_exists():

            raise FileNotFoundError(
                "File invoice tidak ditemukan: "
                f"{invoice_service.file_path}"
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

        text = build_invoice_text(
            invoices
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅ Kembali ke Customer",
                    callback_data="close_detail",
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
                    parse_mode="HTML",
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

                clear_detail_state(
                    context
                )

        message = (
            await query.message.reply_text(
                text=text,
                reply_markup=markup,
                parse_mode="HTML",
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