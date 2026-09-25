import re

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from app.services.search_service import SearchService
from app.services.tunggakan_service import TunggakanService
from app.services.invoice_service import InvoiceService

from app.handlers.admin_handler import (
    show_admin_dashboard,
)

from app.handlers.tunggakan_handler import (
    build_saldo_cyc_text,
    build_saldo_cr_text,
)

from app.handlers.invoice_handler import (
    build_invoice_text,
)


search_service = SearchService()
tunggakan_service = TunggakanService()
invoice_service = InvoiceService()


# =========================================================
# HELPER
# =========================================================

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


def format_periode(value):
    periode = normalize(value)

    if not periode:
        return "-"

    periode = periode.replace(
        ".0",
        "",
    )

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
                f"{month_name} {year}"
            )

    return periode


def get_customer_name_from_result(
    result,
):
    return (
        normalize(
            result.get(
                "customer_name"
            )
        )
        or normalize(
            result.get(
                "PELANGGAN"
            )
        )
        or normalize(
            result.get(
                "pelanggan"
            )
        )
        or "-"
    )


def get_invoice_period(
    context,
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


def build_customer_search_text(
    keyword,
    results,
):
    if not results:
        return (
            "CUSTOMER TIDAK DITEMUKAN\n\n"
            f"Pencarian: {keyword}\n\n"
            "Pastikan nama atau ID pelanggan "
            "sudah benar."
        )

    return (
        "HASIL PENCARIAN CUSTOMER\n\n"
        f"Ditemukan {len(results)} customer.\n"
        "Silakan pilih customer:"
    )


def build_customer_keyboard(
    results,
    command,
):
    keyboard = []

    for result in results:
        customer_id = (
            result.get(
                "customer_id"
            )
            or "-"
        )

        customer_name = (
            result.get(
                "customer_name"
            )
            or "-"
        )

        button_text = (
            f"{customer_name} "
            f"({customer_id})"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    button_text,
                    callback_data=(
                        "command_customer:"
                        f"{command}:"
                        f"{customer_id}"
                    ),
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Kembali",
                callback_data="back_to_ams",
            )
        ]
    )

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# /INV
# =========================================================

async def command_invoice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    keyword,
):
    if not update.message:
        return

    # /inv tanpa keyword
    if not keyword:
        context.user_data[
            "active_menu"
        ] = "invoice"

        context.user_data[
            "customer_page"
        ] = 0

        context.user_data[
            "selected_customer_id"
        ] = None

        from app.handlers.customer_handler import (
            show_customers,
        )

        await show_customers(
            update,
            context,
            page=0,
        )

        return

    # /inv <customer>
    results = (
        search_service
        .search_customers(
            keyword,
            max_results=10,
        )
    )

    if not results:
        await update.message.reply_text(
            build_customer_search_text(
                keyword,
                results,
            )
        )

        return

    # Satu customer
    if len(results) == 1:
        selected = results[0]

        customer_id = (
            selected.get(
                "customer_id"
            )
        )

        if not customer_id:
            await update.message.reply_text(
                "Customer tidak memiliki ID."
            )
            return

        customer_name = (
            get_customer_name_from_result(
                selected
            )
        )

        context.user_data[
            "selected_customer_id"
        ] = customer_id

        context.user_data[
            "active_menu"
        ] = "invoice"

        invoices = (
            invoice_service
            .get_customer_invoice_data(
                customer_id
            )
        )

        if invoices is None:
            invoices = []

        period = get_invoice_period(
            context,
            invoices,
        )

        text = build_invoice_text(
            customer_id=customer_id,
            customer_name=customer_name,
            invoices=invoices,
            period=period,
        )

        await update.message.reply_text(
            text=text
        )

        return

    # Banyak customer
    text = build_customer_search_text(
        keyword,
        results,
    )

    markup = build_customer_keyboard(
        results,
        "invoice",
    )

    await update.message.reply_text(
        text=text,
        reply_markup=markup,
    )


# =========================================================
# /CYC
# =========================================================

async def command_cyc(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    keyword,
):
    if not update.message:
        return

    # /cyc tanpa keyword
    if not keyword:
        context.user_data[
            "active_menu"
        ] = "pelanggan_tunggakan"

        context.user_data[
            "customer_page"
        ] = 0

        context.user_data[
            "selected_customer_id"
        ] = None

        from app.handlers.customer_handler import (
            show_customers,
        )

        await show_customers(
            update,
            context,
            page=0,
        )

        return

    # /cyc <customer>
    results = (
        search_service
        .search_customers(
            keyword,
            max_results=10,
        )
    )

    if not results:
        await update.message.reply_text(
            build_customer_search_text(
                keyword,
                results,
            )
        )

        return

    # Satu customer
    if len(results) == 1:
        selected = results[0]

        customer_id = (
            selected.get(
                "customer_id"
            )
        )

        if not customer_id:
            await update.message.reply_text(
                "Customer tidak memiliki ID."
            )
            return

        context.user_data[
            "selected_customer_id"
        ] = customer_id

        context.user_data[
            "active_menu"
        ] = "pelanggan_tunggakan"

        result = (
            tunggakan_service
            .get_saldo_cyc(
                customer_id
            )
        )

        text = build_saldo_cyc_text(
            result
        )

        await update.message.reply_text(
            text=text
        )

        return

    # Banyak customer
    text = build_customer_search_text(
        keyword,
        results,
    )

    markup = build_customer_keyboard(
        results,
        "cyc",
    )

    await update.message.reply_text(
        text=text,
        reply_markup=markup,
    )


# =========================================================
# /CR
# =========================================================

async def command_cr(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    keyword,
):
    if not update.message:
        return

    # /cr tanpa keyword
    if not keyword:
        context.user_data[
            "active_menu"
        ] = "saldo_cr"

        context.user_data[
            "customer_page"
        ] = 0

        context.user_data[
            "selected_customer_id"
        ] = None

        from app.handlers.customer_handler import (
            show_customers,
        )

        await show_customers(
            update,
            context,
            page=0,
        )

        return

    # /cr <customer>
    results = (
        search_service
        .search_customers(
            keyword,
            max_results=10,
        )
    )

    if not results:
        await update.message.reply_text(
            build_customer_search_text(
                keyword,
                results,
            )
        )

        return

    # Satu customer
    if len(results) == 1:
        selected = results[0]

        customer_id = (
            selected.get(
                "customer_id"
            )
        )

        if not customer_id:
            await update.message.reply_text(
                "Customer tidak memiliki ID."
            )
            return

        context.user_data[
            "selected_customer_id"
        ] = customer_id

        context.user_data[
            "active_menu"
        ] = "saldo_cr"

        result = (
            tunggakan_service
            .get_saldo_cr(
                customer_id
            )
        )

        text = build_saldo_cr_text(
            result
        )

        await update.message.reply_text(
            text=text
        )

        return

    # Banyak customer
    text = build_customer_search_text(
        keyword,
        results,
    )

    markup = build_customer_keyboard(
        results,
        "saldo_cr",
    )

    await update.message.reply_text(
        text=text,
        reply_markup=markup,
    )


# =========================================================
# /AM
# =========================================================

async def command_am(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    keyword,
    show_menu=True,
):
    if not update.message:
        return None

    from app.handlers.customer_handler import (
        show_ams,
        show_customer_menu,
    )

    normalized_keyword = (
        search_service
        .normalize_text(
            keyword
        )
    )

    # /am semua
    if normalized_keyword in (
        "semua",
        "semua am",
    ):
        context.user_data[
            "current_am"
        ] = "__ALL__"

        context.user_data[
            "customer_page"
        ] = 0

        context.user_data[
            "selected_customer_id"
        ] = None

        if show_menu:
            context.user_data[
                "active_menu"
            ] = None

            await show_customer_menu(
                update,
                context,
            )

        return "__ALL__"

    # /am
    if not keyword:
        await show_ams(
            update,
            context,
            page=0,
        )

        return None

    # /am <nama AM>
    results = (
        search_service
        .search_ams(
            keyword,
            max_results=10,
        )
    )

    if not results:
        await update.message.reply_text(
            "AM TIDAK DITEMUKAN\n\n"
            f"Pencarian: {keyword}\n\n"
            "Pastikan nama AM sudah benar."
        )

        return None

    # Satu AM
    if len(results) == 1:
        am_name = results[0].get(
            "am"
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

        if show_menu:
            context.user_data[
                "active_menu"
            ] = None

            await show_customer_menu(
                update,
                context,
            )

        return am_name

    # Banyak AM
    text = (
        "HASIL PENCARIAN AM\n\n"
        f"Ditemukan {len(results)} AM.\n"
        "Silakan pilih:"
    )

    keyboard = []

    for result in results:
        am = result.get(
            "am"
        )

        if not am:
            continue

        keyboard.append(
            [
                InlineKeyboardButton(
                    am,
                    callback_data=(
                        f"select_am:{am}"
                    ),
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "Kembali",
                callback_data="back_to_ams",
            )
        ]
    )

    await update.message.reply_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )

    return None


# =========================================================
# /HELP
# =========================================================

async def command_help(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    text = (
        "BANTUAN COMMAND\n\n"

        "/start\n"
        "Membuka menu utama.\n\n"

        "/inv\n"
        "Melihat daftar invoice.\n\n"

        "/inv <customer>\n"
        "Mencari invoice customer.\n\n"

        "/inv <ID>\n"
        "Mencari invoice berdasarkan ID.\n\n"

        "/cyc\n"
        "Melihat daftar Saldo CYC.\n\n"

        "/cyc <customer>\n"
        "Mencari Saldo CYC customer.\n\n"

        "/cyc <ID>\n"
        "Mencari Saldo CYC berdasarkan ID.\n\n"

        "/cr\n"
        "Melihat daftar Saldo CR.\n\n"

        "/cr <customer>\n"
        "Mencari Saldo CR customer.\n\n"

        "/cr <ID>\n"
        "Mencari Saldo CR berdasarkan ID.\n\n"

        "/am\n"
        "Melihat daftar AM.\n\n"

        "/am semua\n"
        "Melihat seluruh daftar AM.\n\n"

        "/am <nama AM>\n"
        "Mencari AM."
    )

    await update.message.reply_text(
        text
    )


# =========================================================
# MAIN COMMAND ROUTER
# =========================================================

async def command_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    text = (
        update.message.text
        or ""
    ).strip()

    if not text:
        return

    pattern = (
        r"(/[A-Za-z0-9_]+(?:@[A-Za-z0-9_]+)?)"
        r"(.*?)(?=\s+/[A-Za-z0-9_]+"
        r"(?:@[A-Za-z0-9_]+)?(?:\s|$)|$)"
    )

    matches = re.findall(
        pattern,
        text,
        flags=re.DOTALL,
    )

    if not matches:
        return

    commands = []

    for raw_command, raw_keyword in matches:
        command = (
            raw_command
            .lower()
            .split("@")[0]
        )

        keyword = raw_keyword.strip()

        commands.append(
            {
                "command": command,
                "keyword": keyword,
            }
        )

    for index, item in enumerate(
        commands
    ):
        command = item[
            "command"
        ]

        keyword = item[
            "keyword"
        ]

        print(
            "[COMMAND] "
            f"command={command} "
            f"keyword={keyword}"
        )

        # /inv
        if command == "/inv":
            await command_invoice(
                update,
                context,
                keyword,
            )
            continue

        # /cyc
        if command == "/cyc":
            await command_cyc(
                update,
                context,
                keyword,
            )
            continue

        # /cr
        if command == "/cr":
            await command_cr(
                update,
                context,
                keyword,
            )
            continue

        # /am
        if command == "/am":
            has_next_command = (
                index + 1
                < len(commands)
            )

            next_command = None

            if has_next_command:
                next_command = commands[
                    index + 1
                ][
                    "command"
                ]

            if next_command in (
                "/inv",
                "/cyc",
                "/cr",
            ):
                await command_am(
                    update,
                    context,
                    keyword,
                    show_menu=False,
                )
            else:
                await command_am(
                    update,
                    context,
                    keyword,
                    show_menu=True,
                )

            continue

        # /acc
        if command == "/acc":
            print(
                "[ADMIN] "
                "Opening admin dashboard..."
            )

            await show_admin_dashboard(
                update,
                context,
            )

            continue

        # /help
        if command == "/help":
            await command_help(
                update,
                context,
            )

            continue

        print(
            "[COMMAND] "
            f"Command tidak dikenali: {command}"
        )