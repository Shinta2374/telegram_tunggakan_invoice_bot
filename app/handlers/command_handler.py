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

from app.handlers.tunggakan_handler import (
    build_tunggakan_text,
    format_rupiah,
)

from app.handlers.invoice_handler import (
    build_invoice_text,
    get_customer_by_id,
    get_customer_name,
    get_invoice_period,
)


search_service = SearchService()
tunggakan_service = TunggakanService()
invoice_service = InvoiceService()


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
            result.get("customer_id")
            or "-"
        )

        customer_name = (
            result.get("customer_name")
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


def build_cyc_text(
    result,
    customer_id,
):
    if not result:
        return (
            "INFORMASI SALDO CYC\n\n"
            f"ID: {customer_id}\n\n"
            "Data CYC tidak ditemukan."
        )

    pelanggan = (
        result.get("PELANGGAN")
        or result.get("pelanggan")
        or "-"
    )

    idnumber = (
        result.get("idnumber")
        or customer_id
    )

    am = (
        result.get("am")
        or "-"
    )

    saldo = result.get(
        "saldo_akhir_cyc",
        0,
    )

    return (
        "INFORMASI SALDO CYC\n\n"
        f"{pelanggan} ({idnumber})\n"
        f"{am}\n\n"
        f"Saldo Akhir CYC: "
        f"{format_rupiah(saldo)}"
    )


async def command_tunggakan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    keyword,
):
    if not update.message:
        return

    if not keyword:
        context.user_data[
            "active_menu"
        ] = "tunggakan"

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

    if len(results) == 1:
        selected = results[0]

        customer_id = (
            selected["customer_id"]
        )

        context.user_data[
            "selected_customer_id"
        ] = customer_id

        context.user_data[
            "active_menu"
        ] = "tunggakan"

        result = (
            tunggakan_service
            .get_tunggakan(
                customer_id
            )
        )

        if not result:
            await update.message.reply_text(
                "Data tunggakan tidak ditemukan."
            )

            return

        text = build_tunggakan_text(
            result
        )

        await update.message.reply_text(
            text=text
        )

        return

    text = build_customer_search_text(
        keyword,
        results,
    )

    markup = build_customer_keyboard(
        results,
        "tunggakan",
    )

    await update.message.reply_text(
        text=text,
        reply_markup=markup,
    )


async def command_invoice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    keyword,
):
    if not update.message:
        return

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

    if len(results) == 1:
        selected = results[0]

        customer_id = (
            selected["customer_id"]
        )

        context.user_data[
            "selected_customer_id"
        ] = customer_id

        context.user_data[
            "active_menu"
        ] = "invoice"

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
            customer_name = (
                selected.get(
                    "customer_name"
                )
                or "-"
            )

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


async def command_cyc(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    keyword,
):
    if not update.message:
        return

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

    if len(results) == 1:
        selected = results[0]

        customer_id = (
            selected["customer_id"]
        )

        context.user_data[
            "selected_customer_id"
        ] = customer_id

        context.user_data[
            "active_menu"
        ] = "pelanggan_tunggakan"

        result = (
            tunggakan_service
            .get_tunggakan(
                customer_id
            )
        )

        text = build_cyc_text(
            result,
            customer_id,
        )

        await update.message.reply_text(
            text=text
        )

        return

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
        .normalize_text(keyword)
    )

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

    if not keyword:
        await show_ams(
            update,
            context,
            page=0,
        )

        return None

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

    if len(results) == 1:
        am_name = results[0]["am"]

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

    text = (
        "HASIL PENCARIAN AM\n\n"
        f"Ditemukan {len(results)} AM.\n"
        "Silakan pilih:"
    )

    keyboard = []

    for result in results:
        am = result["am"]

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


async def command_customer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    keyword,
):
    if not update.message:
        return

    if not keyword:
        await update.message.reply_text(
            "CARI CUSTOMER\n\n"
            "Gunakan format:\n\n"
            "/cust <nama customer>\n"
            "/cust <ID pelanggan>\n\n"
            "Contoh:\n"
            "/cust palmyra\n"
            "/cust 5003595"
        )

        return

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

    if len(results) == 1:
        result = results[0]

        customer_name = (
            result.get(
                "customer_name"
            )
            or "-"
        )

        customer_id = (
            result.get(
                "customer_id"
            )
            or "-"
        )

        am = (
            result.get(
                "am"
            )
            or "-"
        )

        text = (
            "CUSTOMER DITEMUKAN\n\n"
            f"{customer_name} "
            f"({customer_id})\n"
            f"{am}"
        )

        await update.message.reply_text(
            text=text
        )

        return

    text = build_customer_search_text(
        keyword,
        results,
    )

    markup = build_customer_keyboard(
        results,
        "customer",
    )

    await update.message.reply_text(
        text=text,
        reply_markup=markup,
    )


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

        "/tgkn\n"
        "Melihat daftar tunggakan.\n\n"

        "/tgkn <customer>\n"
        "Mencari tunggakan customer.\n\n"

        "/tgkn <ID>\n"
        "Mencari tunggakan berdasarkan ID.\n\n"

        "/inv\n"
        "Melihat daftar invoice.\n\n"

        "/inv <customer>\n"
        "Mencari invoice customer.\n\n"

        "/inv <ID>\n"
        "Mencari invoice berdasarkan ID.\n\n"

        "/cyc\n"
        "Melihat saldo CYC.\n\n"

        "/cyc <customer>\n"
        "Mencari saldo CYC customer.\n\n"

        "/cyc <ID>\n"
        "Mencari saldo CYC berdasarkan ID.\n\n"

        "/am\n"
        "Melihat daftar AM.\n\n"

        "/am semua\n"
        "Melihat seluruh daftar AM.\n\n"

        "/am <nama AM>\n"
        "Mencari AM.\n\n"

        "/cust <customer>\n"
        "Mencari customer.\n\n"

        "/cust <ID>\n"
        "Mencari customer berdasarkan ID.\n\n"

        "/help\n"
        "Menampilkan bantuan command."
    )

    await update.message.reply_text(
        text
    )


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
        r"(.*?)(?=\s+/[A-Za-z0-9_]+(?:@[A-Za-z0-9_]+)?(?:\s|$)|$)"
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

    for index, item in enumerate(commands):

        command = item["command"]
        keyword = item["keyword"]

        print(
            "[COMMAND] "
            f"command={command} "
            f"keyword={keyword}"
        )

        if command == "/am":

            has_next_command = (
                index + 1
                < len(commands)
            )

            next_command = None

            if has_next_command:
                next_command = commands[
                    index + 1
                ]["command"]

            if next_command in (
                "/tgkn",
                "/inv",
                "/cyc",
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

        if command == "/tgkn":

            await command_tunggakan(
                update,
                context,
                keyword,
            )

            continue

        if command == "/inv":

            await command_invoice(
                update,
                context,
                keyword,
            )

            continue

        if command == "/cyc":

            await command_cyc(
                update,
                context,
                keyword,
            )

            continue

        if command == "/cust":

            await command_customer(
                update,
                context,
                keyword,
            )

            continue

        if command == "/help":

            await command_help(
                update,
                context,
            )

            continue