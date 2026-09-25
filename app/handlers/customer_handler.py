import pandas as pd

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from app.services.customer_service import CustomerService
from app.services.invoice_service import InvoiceService


customer_service = CustomerService()
invoice_service = InvoiceService()

CUSTOMERS_PER_PAGE = 6
AMS_PER_PAGE = 6

ALL_AM = "__ALL__"


def normalize(value):
    if value is None:
        return ""

    if pd.isna(value):
        return ""

    value = str(value).strip()

    if value.lower() in (
        "nan",
        "none",
    ):
        return ""

    return value


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


def normalize_am(value):
    value = normalize(value)

    if not value:
        return ""

    value = value.lower()

    if value.startswith("am "):
        value = value[3:].strip()

    return value


def get_customer_name(customer):
    return (
        normalize(
            customer.get("PELANGGAN")
        )
        or normalize(
            customer.get("pelanggan")
        )
        or normalize(
            customer.get("nama")
        )
        or normalize(
            customer.get("CUSTOMER")
        )
        or normalize(
            customer.get("pcTCYC")
        )
        or normalize(
            customer.get("contr_account_detail")
        )
        or "-"
    )


def get_customer_am(customer):
    return (
        normalize(
            customer.get("AM")
        )
        or normalize(
            customer.get("am")
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


def to_number(value):
    if value is None:
        return 0

    try:
        if isinstance(value, bool):
            return 0

        if isinstance(value, (int, float)):
            if pd.isna(value):
                return 0

            return float(value)

        value = str(value).strip()

        if not value:
            return 0

        value = (
            value
            .replace("Rp", "")
            .replace("rp", "")
            .replace(" ", "")
        )

        if "." in value and "," not in value:
            parts = value.split(".")

            if all(
                len(part) == 3
                for part in parts[1:]
            ):
                value = "".join(parts)

        elif "." in value and "," in value:
            value = (
                value
                .replace(".", "")
                .replace(",", ".")
            )

        elif "," in value:
            value = value.replace(
                ",",
                ".",
            )

        return float(value)

    except (
        ValueError,
        TypeError,
    ):
        return 0


def format_rupiah(value):
    number = to_number(value)

    return (
        f"Rp{number:,.0f}"
        .replace(",", ".")
    )


def get_tunggakan_total(customer):
    return to_number(
        customer.get(
            "SALDO AKHIR CYC"
        )
    )


def get_saldo_cr_total(customer):
    return to_number(
        customer.get(
            "saldo_akhir"
        )
    )


def group_customers_by_am(customers):
    groups = {}

    for customer in customers:
        am = get_customer_am(
            customer
        )

        if not am or am == "-":
            continue

        if am not in groups:
            groups[am] = []

        groups[am].append(
            customer
        )

    return groups


def get_invoice_customers(
    current_am,
):
    invoice_customers = (
        invoice_service
        .get_invoice_customers()
    )

    if not invoice_customers:
        return []

    if current_am == ALL_AM:
        return invoice_customers

    customers = (
        customer_service
        .get_all_customers()
    )

    am_by_customer_id = {}

    for customer in customers:
        customer_id = get_customer_id(
            customer
        )

        if customer_id == "-":
            continue

        am_by_customer_id[
            customer_id
        ] = get_customer_am(
            customer
        )

    target_am = normalize_am(
        current_am
    )

    filtered = []

    for invoice_customer in invoice_customers:
        customer_id = get_customer_id(
            invoice_customer
        )

        customer_am = (
            am_by_customer_id.get(
                customer_id,
                "",
            )
        )

        if normalize_am(
            customer_am
        ) == target_am:
            customer_copy = dict(
                invoice_customer
            )

            customer_copy["AM"] = (
                customer_am
            )

            filtered.append(
                customer_copy
            )

    return filtered


def get_filtered_customers(
    customers,
    current_am,
    active_menu,
):
    if (
        current_am != ALL_AM
        and active_menu != "invoice"
    ):
        target_am = normalize_am(
            current_am
        )

        customers = [
            customer
            for customer in customers
            if normalize_am(
                get_customer_am(
                    customer
                )
            ) == target_am
        ]

    # ==========================================
    # FILTER MENU SALDO CYC
    # ==========================================

    if active_menu == "pelanggan_tunggakan":
        customers = [
            customer
            for customer in customers
            if get_tunggakan_total(
                customer
            ) != 0
        ]

        customers.sort(
            key=get_tunggakan_total,
            reverse=True,
        )

    # ==========================================
    # FILTER MENU SALDO CR
    # ==========================================

    elif active_menu == "saldo_cr":
        customers = [
            customer
            for customer in customers
            if get_saldo_cr_total(
                customer
            ) != 0
        ]

        customers.sort(
            key=get_saldo_cr_total,
            reverse=True,
        )

    # ==========================================
    # LEGACY TUNGGAKAN
    # ==========================================

    elif active_menu == "tunggakan":
        customers.sort(
            key=get_tunggakan_total,
            reverse=True,
        )

    else:
        customers.sort(
            key=lambda customer: (
                get_customer_name(
                    customer
                ).lower()
            )
        )

    return customers


async def show_ams(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int = 0,
    search_results=None,
):
    if search_results is not None:
        ams = sorted(
            search_results,
            key=str.lower,
        )

    else:
        customers = (
            customer_service
            .get_all_customers()
        )

        groups = group_customers_by_am(
            customers
        )

        ams = sorted(
            groups.keys(),
            key=str.lower,
        )

    total_ams = len(ams)

    if total_ams == 0:
        text = (
            "PILIH AM\n\n"
            "Tidak ada data AM."
        )

        if update.callback_query:
            await (
                update.callback_query
                .edit_message_text(
                    text=text
                )
            )
        else:
            await update.message.reply_text(
                text
            )

        return

    total_pages = (
        total_ams
        + AMS_PER_PAGE
        - 1
    ) // AMS_PER_PAGE

    page = max(
        0,
        min(
            page,
            total_pages - 1,
        ),
    )

    start_index = (
        page * AMS_PER_PAGE
    )

    end_index = min(
        start_index + AMS_PER_PAGE,
        total_ams,
    )

    page_ams = ams[
        start_index:end_index
    ]

    text = (
        "PILIH AM\n\n"
        f"Menampilkan "
        f"{start_index + 1}–"
        f"{end_index} dari "
        f"{total_ams} AM"
    )

    keyboard = []

    row = []

    for am in page_ams:
        display_name = normalize(am)

        if display_name.upper().startswith(
            "AM "
        ):
            display_name = (
                display_name[3:]
                .strip()
            )

        row.append(
            InlineKeyboardButton(
                display_name,
                callback_data=(
                    f"select_am:{am}"
                ),
            )
        )

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "Sebelumnya",
                callback_data=(
                    f"am_page:{page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"{page + 1}/{total_pages}",
            callback_data="noop",
        )
    )

    if page < total_pages - 1:
        navigation.append(
            InlineKeyboardButton(
                "Selanjutnya",
                callback_data=(
                    f"am_page:{page + 1}"
                ),
            )
        )

    keyboard.append(
        navigation
    )

    if search_results is None:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Semua",
                    callback_data=(
                        f"select_am:{ALL_AM}"
                    ),
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Cari AM",
                callback_data="search_am",
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    if update.callback_query:
        await (
            update.callback_query
            .edit_message_text(
                text=text,
                reply_markup=reply_markup,
            )
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
        )


async def show_customer_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    current_am = normalize(
        context.user_data.get(
            "current_am"
        )
    )

    if current_am == ALL_AM:
        display_am = "Semua"

    else:
        display_am = current_am

        if display_am.upper().startswith(
            "AM "
        ):
            display_am = (
                display_am[3:]
                .strip()
            )

    text = (
        f"AM {display_am}\n\n"
        "Pilih menu:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "Invoice",
                callback_data=(
                    "am_menu:invoice"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "Saldo CYC",
                callback_data=(
                    "am_menu:"
                    "pelanggan_tunggakan"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "Saldo CR",
                callback_data=(
                    "am_menu:saldo_cr"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "Kembali",
                callback_data=(
                    "back_to_ams"
                ),
            )
        ],
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    if update.callback_query:
        await (
            update.callback_query
            .edit_message_text(
                text=text,
                reply_markup=reply_markup,
            )
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
        )


async def show_customers(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int = 0,
    message_id=None,
    chat_id=None,
):
    current_am = normalize(
        context.user_data.get(
            "current_am"
        )
    )

    active_menu = normalize(
        context.user_data.get(
            "active_menu"
        )
    )

    if not current_am:
        await show_ams(
            update,
            context,
            page=0,
        )
        return

    if not active_menu:
        await show_customer_menu(
            update,
            context,
        )
        return

    if active_menu == "invoice":
        customers = get_invoice_customers(
            current_am
        )
    else:
        customers = (
            customer_service
            .get_all_customers()
        )

        customers = get_filtered_customers(
            customers,
            current_am,
            active_menu,
        )

    total_customers = len(
        customers
    )

    if active_menu == "invoice":
        title = "INVOICE"

    elif active_menu == "pelanggan_tunggakan":
        title = "SALDO CYC"

    elif active_menu == "saldo_cr":
        title = "SALDO CR"

    elif active_menu == "tunggakan":
        title = "TUNGGAKAN"

    else:
        title = "CUSTOMER"

    if current_am == ALL_AM:
        am_text = "Semua"

    else:
        am_text = current_am

        if am_text.upper().startswith(
            "AM "
        ):
            am_text = (
                am_text[3:]
                .strip()
            )

    if total_customers == 0:
        text = (
            f"{title}\n"
            f"AM {am_text}\n\n"
            "Tidak ada data."
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Kembali",
                    callback_data=(
                        "back_to_customer_menu"
                    ),
                )
            ]
        ]

        reply_markup = InlineKeyboardMarkup(
            keyboard
        )

        if message_id and chat_id:
            try:
                await (
                    update.get_bot()
                    .edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=text,
                        reply_markup=reply_markup,
                    )
                )
            except Exception as error:
                if (
                    "Message is not modified"
                    not in str(error)
                ):
                    raise

        elif update.callback_query:
            try:
                await (
                    update.callback_query
                    .edit_message_text(
                        text=text,
                        reply_markup=reply_markup,
                    )
                )
            except Exception as error:
                if (
                    "Message is not modified"
                    not in str(error)
                ):
                    raise

        else:
            await update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
            )

        return

    total_pages = (
        total_customers
        + CUSTOMERS_PER_PAGE
        - 1
    ) // CUSTOMERS_PER_PAGE

    page = max(
        0,
        min(
            page,
            total_pages - 1,
        ),
    )

    context.user_data[
        "customer_page"
    ] = page

    start_index = (
        page * CUSTOMERS_PER_PAGE
    )

    end_index = min(
        start_index + CUSTOMERS_PER_PAGE,
        total_customers,
    )

    page_customers = customers[
        start_index:end_index
    ]

    text = (
        f"MENU {title} AM "
        f"{am_text}\n\n"
        f"Menampilkan "
        f"{start_index + 1}–"
        f"{end_index} dari "
        f"{total_customers} pelanggan"
    )

    keyboard = []

    # ==========================================
    # HEADER SALDO CYC
    # ==========================================

    if active_menu == "pelanggan_tunggakan":
        keyboard.append(
            [
                InlineKeyboardButton(
                    "PELANGGAN",
                    callback_data="noop",
                ),
                InlineKeyboardButton(
                    "SALDO CYC",
                    callback_data="noop",
                ),
            ]
        )

    # ==========================================
    # HEADER SALDO CR
    # ==========================================

    elif active_menu == "saldo_cr":
        keyboard.append(
            [
                InlineKeyboardButton(
                    "PELANGGAN",
                    callback_data="noop",
                ),
                InlineKeyboardButton(
                    "SALDO CR",
                    callback_data="noop",
                ),
            ]
        )

    for customer in page_customers:
        nama = get_customer_name(
            customer
        )

        customer_id = get_customer_id(
            customer
        )

        if active_menu == "pelanggan_tunggakan":
            total = get_tunggakan_total(
                customer
            )

            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{nama} ({customer_id})",
                        callback_data=(
                            "customer_select:"
                            f"{customer_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        format_rupiah(total),
                        callback_data="noop",
                    ),
                ]
            )

        elif active_menu == "saldo_cr":
            total = get_saldo_cr_total(
                customer
            )

            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{nama} ({customer_id})",
                        callback_data=(
                            "customer_select:"
                            f"{customer_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        format_rupiah(total),
                        callback_data="noop",
                    ),
                ]
            )

        else:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{nama} ({customer_id})",
                        callback_data=(
                            "customer_select:"
                            f"{customer_id}"
                        ),
                    )
                ]
            )

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "Sebelumnya",
                callback_data=(
                    f"customer_page:{page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"{page + 1}/{total_pages}",
            callback_data="noop",
        )
    )

    if page < total_pages - 1:
        navigation.append(
            InlineKeyboardButton(
                "Selanjutnya",
                callback_data=(
                    f"customer_page:{page + 1}"
                ),
            )
        )

    keyboard.append(
        navigation
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Cari Customer",
                callback_data="search_customer",
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Kembali",
                callback_data=(
                    "back_to_customer_menu"
                ),
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    try:
        if message_id and chat_id:
            await (
                update.get_bot()
                .edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    reply_markup=reply_markup,
                )
            )

        elif update.callback_query:
            await (
                update.callback_query
                .edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                )
            )

        else:
            await update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
            )

    except Exception as error:
        if (
            "Message is not modified"
            in str(error)
        ):
            print(
                "[CUSTOMER LIST] "
                "Pesan sudah dalam kondisi "
                "yang sama."
            )
        else:
            raise

    if (
        update.callback_query
        and update.callback_query.message
    ):
        context.user_data[
            "customer_list_message_id"
        ] = (
            update
            .callback_query
            .message
            .message_id
        )

        context.user_data[
            "customer_list_chat_id"
        ] = (
            update
            .callback_query
            .message
            .chat_id
        )

    elif message_id and chat_id:
        context.user_data[
            "customer_list_message_id"
        ] = message_id

        context.user_data[
            "customer_list_chat_id"
        ] = chat_id


async def search_customers(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    keyword: str,
):
    keyword = normalize(
        keyword
    ).lower()

    if not keyword:
        await update.message.reply_text(
            "Kata pencarian tidak boleh kosong."
        )
        return

    current_am = normalize(
        context.user_data.get(
            "current_am"
        )
    )

    active_menu = normalize(
        context.user_data.get(
            "active_menu"
        )
    )

    if active_menu == "invoice":
        customers = get_invoice_customers(
            current_am
        )

    else:
        customers = (
            customer_service
            .get_all_customers()
        )

        customers = get_filtered_customers(
            customers,
            current_am,
            active_menu,
        )

    results = []

    for customer in customers:
        nama = get_customer_name(
            customer
        ).lower()

        customer_id = get_customer_id(
            customer
        ).lower()

        am = get_customer_am(
            customer
        ).lower()

        if (
            keyword in nama
            or keyword in customer_id
            or keyword in am
        ):
            results.append(
                customer
            )

    if not results:
        await update.message.reply_text(
            "Customer tidak ditemukan.\n\n"
            f"Pencarian: {keyword}"
        )
        return

    text = (
        "HASIL PENCARIAN CUSTOMER\n\n"
        f"Menemukan {len(results)} customer"
    )

    keyboard = []

    for customer in results[:10]:
        nama = get_customer_name(
            customer
        )

        customer_id = get_customer_id(
            customer
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{nama} ({customer_id})",
                    callback_data=(
                        "customer_select:"
                        f"{customer_id}"
                    ),
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Kembali",
                callback_data=(
                    "back_to_customer_menu"
                ),
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup,
    )


async def show_customer_info(
    query,
    context: ContextTypes.DEFAULT_TYPE,
):
    customer_id = (
        context.user_data.get(
            "selected_customer_id"
        )
    )

    if not customer_id:
        print(
            "[CUSTOMER INFO ERROR] "
            "ID Pelanggan belum tersedia."
        )
        return

    customers = (
        customer_service
        .get_all_customers()
    )

    target_customer = None

    target_id = normalize_id(
        customer_id
    )

    for customer in customers:
        current_id = get_customer_id(
            customer
        )

        if current_id == target_id:
            target_customer = customer
            break

    if not target_customer:
        print(
            "[CUSTOMER INFO ERROR] "
            f"Customer {customer_id} tidak ditemukan."
        )
        return

    pelanggan = get_customer_name(
        target_customer
    )

    am = get_customer_am(
        target_customer
    )

    text = (
        "INFORMASI PELANGGAN\n\n"
        f"{pelanggan} ({target_id})\n"
        f"{am}"
    )

    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Kembali",
                    callback_data=(
                        "back_to_customer_list"
                    ),
                )
            ]
        ]
    )

    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
        )

        context.user_data[
            "detail_message_id"
        ] = query.message.message_id

        context.user_data[
            "detail_chat_id"
        ] = query.message.chat_id

        context.user_data[
            "detail_type"
        ] = "customer"

    except Exception as error:
        if (
            "Message is not modified"
            in str(error)
        ):
            pass
        else:
            print(
                f"[CUSTOMER INFO ERROR] {error}"
            )


async def restore_customer_list(
    query,
    context: ContextTypes.DEFAULT_TYPE,
):
    list_message_id = (
        context.user_data.get(
            "customer_list_message_id"
        )
    )

    list_chat_id = (
        context.user_data.get(
            "customer_list_chat_id"
        )
    )

    page = context.user_data.get(
        "customer_page",
        0,
    )

    if not list_message_id:
        print(
            "[LIST] "
            "ID pesan list tidak ditemukan."
        )
        return

    if not list_chat_id:
        print(
            "[LIST] "
            "Chat ID list tidak ditemukan."
        )
        return

    try:
        await show_customers(
            update=query,
            context=context,
            page=page,
            message_id=list_message_id,
            chat_id=list_chat_id,
        )

    except Exception as error:
        if (
            "Message is not modified"
            not in str(error)
        ):
            print(
                f"[RESTORE LIST ERROR] {error}"
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