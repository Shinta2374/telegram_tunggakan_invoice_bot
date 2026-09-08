from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from app.services.customer_service import CustomerService


customer_service = CustomerService()

CUSTOMERS_PER_PAGE = 6
AMS_PER_PAGE = 6

ALL_AM = "__ALL__"


def normalize(value):
    if value is None:
        return ""

    return str(value).strip()


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
        normalize(customer.get("PELANGGAN"))
        or normalize(customer.get("nama"))
        or normalize(customer.get("CUSTOMER"))
        or normalize(customer.get("pcTCYC"))
        or "-"
    )


def get_customer_am(customer):
    return (
        normalize(customer.get("AM"))
        or normalize(customer.get("am"))
        or "-"
    )


def get_customer_id(customer):
    return (
        normalize(customer.get("idnumber"))
        or normalize(customer.get("ID"))
        or normalize(customer.get("id"))
        or "-"
    )


def to_number(value):
    if value is None:
        return 0

    try:
        if isinstance(value, float):
            if value != value:
                return 0

            return value

        value = str(value).strip()

        if not value:
            return 0

        value = (
            value
            .replace("Rp", "")
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
            value = value.replace(",", ".")

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
        customer.get("SALDO AKHIR CYC")
    )


def group_customers_by_am(customers):
    groups = {}

    for customer in customers:
        am = get_customer_am(customer)

        if not am or am == "-":
            continue

        if am not in groups:
            groups[am] = []

        groups[am].append(customer)

    return groups


def get_filtered_customers(
    customers,
    current_am,
    active_menu,
):
    if current_am != ALL_AM:

        target_am = normalize_am(
            current_am
        )

        customers = [
            customer
            for customer in customers
            if normalize_am(
                get_customer_am(customer)
            ) == target_am
        ]

    if active_menu == "pelanggan_tunggakan":

        customers = [
            customer
            for customer in customers
            if get_tunggakan_total(
                customer
            ) > 0
        ]

        customers.sort(
            key=get_tunggakan_total,
            reverse=True,
        )

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

            await update.callback_query.edit_message_text(
                text=text
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

        if display_name.upper().startswith("AM "):

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

    if navigation:
        keyboard.append(navigation)

    if search_results is None:

        keyboard.append(
            [
                InlineKeyboardButton(
                    "Semua AM",
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

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
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

        display_am = "Semua AM"

    else:

        display_am = current_am

        if display_am.upper().startswith("AM "):

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
                    "customer_menu:invoice"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "Tunggakan",
                callback_data=(
                    "customer_menu:tunggakan"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "Saldo CYC",
                callback_data=(
                    "customer_menu:"
                    "pelanggan_tunggakan"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "Kembali",
                callback_data="back_to_ams",
            )
        ],
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    if update.callback_query:

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
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
    customers = (
        customer_service
        .get_all_customers()
    )

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

    customers = get_filtered_customers(
        customers,
        current_am,
        active_menu,
    )

    total_customers = len(customers)

    if active_menu == "invoice":

        title = "INVOICE"

    elif active_menu == "tunggakan":

        title = "TUNGGAKAN"

    elif active_menu == "pelanggan_tunggakan":

        title = "PELANGGAN DENGAN TUNGGAKAN AM"

    else:

        title = "CUSTOMER"

    if current_am == ALL_AM:

        am_text = "Semua AM"

    else:

        am_text = current_am

        if am_text.upper().startswith("AM "):

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

            await update.get_bot().edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
            )

        elif update.callback_query:

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
            )

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

    if active_menu == "pelanggan_tunggakan":

        text = (
            f"SALDO CYC AM {am_text}\n\n"
            f"Menampilkan "
            f"{start_index + 1}–"
            f"{end_index} dari "
            f"{total_customers} pelanggan"
        )

    else:

        text = (
            f"MENU {title} AM "
            f"{am_text}\n\n"
            f"Menampilkan "
            f"{start_index + 1}–"
            f"{end_index} dari "
            f"{total_customers} pelanggan"
        )

    keyboard = []

    if active_menu == "pelanggan_tunggakan":

        keyboard.append(
            [
                InlineKeyboardButton(
                    "PELANGGAN",
                    callback_data="noop",
                ),
                InlineKeyboardButton(
                    "TUNGGAKAN",
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

            customer_button = InlineKeyboardButton(
                f"{nama} ({customer_id})",
                callback_data=(
                    f"customer_select:"
                    f"{customer_id}"
                ),
            )

            saldo_button = InlineKeyboardButton(
                format_rupiah(total),
                callback_data="noop",
            )

            keyboard.append(
                [
                    customer_button,
                    saldo_button,
                ]
            )

        elif active_menu == "tunggakan":

            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{nama} ({customer_id})",
                        callback_data=(
                            f"customer_select:"
                            f"{customer_id}"
                        ),
                    )
                ]
            )

        else:

            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{nama} ({customer_id})",
                        callback_data=(
                            f"customer_select:"
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

    if navigation:
        keyboard.append(navigation)

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

    if message_id and chat_id:

        await update.get_bot().edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
        )

    elif update.callback_query:

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
        )

    else:

        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
        )


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

    customers = (
        customer_service
        .get_all_customers()
    )

    current_am = normalize(
        context.user_data.get(
            "current_am"
        )
    )

    if (
        current_am
        and current_am != ALL_AM
    ):

        target_am = normalize_am(
            current_am
        )

        customers = [
            customer
            for customer in customers
            if normalize_am(
                get_customer_am(customer)
            ) == target_am
        ]

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
                        f"customer_select:"
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