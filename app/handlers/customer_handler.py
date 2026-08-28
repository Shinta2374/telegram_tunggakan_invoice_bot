"""
Handler daftar AM dan customer.
"""

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from app.services.customer_service import CustomerService


customer_service = CustomerService()

CUSTOMERS_PER_PAGE = 4
AMS_PER_PAGE = 6


def normalize(value):
    if value is None:
        return ""

    return str(value).strip()


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


async def show_ams(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int = 0,
    search_results=None,
):
    if search_results is not None:
        ams = sorted(search_results)
    else:
        customers = customer_service.get_all_customers()
        groups = group_customers_by_am(customers)
        ams = sorted(groups.keys())

    if not ams:
        text = (
            "👥 DAFTAR ACCOUNT MANAGER\n\n"
            "Tidak ada data AM."
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text
            )
        else:
            await update.message.reply_text(text)

        return

    total_ams = len(ams)

    total_pages = (
        total_ams + AMS_PER_PAGE - 1
    ) // AMS_PER_PAGE

    page = max(
        0,
        min(page, total_pages - 1)
    )

    start_index = page * AMS_PER_PAGE

    end_index = min(
        start_index + AMS_PER_PAGE,
        total_ams
    )

    page_ams = ams[
        start_index:end_index
    ]

    text = (
        "👥 DAFTAR ACCOUNT MANAGER\n\n"
        f"Menampilkan {start_index + 1}–"
        f"{end_index} dari {total_ams} AM"
    )

    keyboard = []

    for am in page_ams:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"👤 {am}",
                    callback_data=f"select_am:{am}"
                )
            ]
        )

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ Sebelumnya",
                callback_data=f"am_page:{page - 1}"
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"{page + 1}/{total_pages}",
            callback_data="noop"
        )
    )

    if page < total_pages - 1:
        navigation.append(
            InlineKeyboardButton(
                "Selanjutnya ➡️",
                callback_data=f"am_page:{page + 1}"
            )
        )

    keyboard.append(navigation)

    keyboard.append(
        [
            InlineKeyboardButton(
                "🔍 Cari AM",
                callback_data="search_am"
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup
        )


async def show_customers(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int = 0,
):
    customers = customer_service.get_all_customers()

    if not customers:
        text = (
            "👥 CUSTOMER\n\n"
            "Tidak ada data customer."
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text
            )
        else:
            await update.message.reply_text(text)

        return

    groups = group_customers_by_am(customers)

    current_am = normalize(
        context.user_data.get("current_am")
    )

    if not current_am:
        if not groups:
            text = (
                "👥 CUSTOMER\n\n"
                "Tidak ada customer."
            )

            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=text
                )
            else:
                await update.message.reply_text(text)

            return

        current_am = sorted(groups.keys())[0]

        context.user_data["current_am"] = current_am

    if current_am not in groups:
        print(
            f"[CUSTOMER ERROR] AM tidak ditemukan: "
            f"{current_am}"
        )

        await show_ams(
            update,
            context,
            page=0
        )

        return

    am_customers = groups[current_am]

    print(f"[AM] {current_am}")
    print(f"[CUSTOMER AM] {len(am_customers)}")

    total_customers = len(am_customers)

    if total_customers == 0:
        text = (
            "👥 CUSTOMER\n"
            f"AM: {current_am}\n\n"
            "Tidak ada customer."
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text
            )
        else:
            await update.message.reply_text(text)

        return

    total_pages = (
        total_customers + CUSTOMERS_PER_PAGE - 1
    ) // CUSTOMERS_PER_PAGE

    page = max(
        0,
        min(page, total_pages - 1)
    )

    context.user_data["customer_page"] = page

    start_index = page * CUSTOMERS_PER_PAGE

    end_index = min(
        start_index + CUSTOMERS_PER_PAGE,
        total_customers
    )

    page_customers = am_customers[
        start_index:end_index
    ]

    text = (
        "👥 CUSTOMER\n"
        f"AM: {current_am}\n\n"
        f"Menampilkan {start_index + 1}–"
        f"{end_index} dari {total_customers} customer"
    )

    keyboard = []

    for customer in page_customers:
        nama = get_customer_name(customer)
        customer_id = get_customer_id(customer)

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🏢 {nama}\n🆔 {customer_id}",
                    callback_data="noop"
                )
            ]
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "📄 Tunggakan",
                    callback_data=f"tunggakan:{customer_id}"
                ),
                InlineKeyboardButton(
                    "📧 Invoice",
                    callback_data=f"invoice:{customer_id}"
                )
            ]
        )

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ Sebelumnya",
                callback_data=f"customer_page:{page - 1}"
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"{page + 1}/{total_pages}",
            callback_data="noop"
        )
    )

    if page < total_pages - 1:
        navigation.append(
            InlineKeyboardButton(
                "Selanjutnya ➡️",
                callback_data=f"customer_page:{page + 1}"
            )
        )

    keyboard.append(navigation)

    keyboard.append(
        [
            InlineKeyboardButton(
                "🔍 Cari Customer",
                callback_data="search_customer"
            ),
            InlineKeyboardButton(
                "⬅️ AM",
                callback_data="back_to_ams"
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup
        )


async def search_customers(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    keyword: str,
):
    keyword = normalize(keyword).lower()

    if not keyword:
        await update.message.reply_text(
            "❌ Kata pencarian tidak boleh kosong."
        )
        return

    customers = customer_service.get_all_customers()

    results = []

    for customer in customers:
        nama = get_customer_name(customer).lower()
        customer_id = get_customer_id(customer).lower()
        am = get_customer_am(customer).lower()

        if (
            keyword in nama
            or keyword in customer_id
            or keyword in am
        ):
            results.append(customer)

    if not results:
        await update.message.reply_text(
            "🔍 Customer tidak ditemukan.\n\n"
            f"Pencarian: {keyword}"
        )
        return

    text = (
        "🔍 HASIL PENCARIAN CUSTOMER\n\n"
        f"Menemukan {len(results)} customer"
    )

    keyboard = []

    for customer in results[:10]:
        nama = get_customer_name(customer)
        customer_id = get_customer_id(customer)

        text += (
            f"\n\n{nama}\n"
            f"ID: {customer_id}"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🏢 {nama}\n🆔 {customer_id}",
                    callback_data="noop"
                )
            ]
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "📄 Tunggakan",
                    callback_data=f"tunggakan:{customer_id}"
                ),
                InlineKeyboardButton(
                    "📧 Invoice",
                    callback_data=f"invoice:{customer_id}"
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="back_to_customers"
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )