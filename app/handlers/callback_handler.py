from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from app.handlers.auth_handler import handle_auth_callback
from app.handlers.admin_handler import handle_admin_callback

from app.handlers.customer_handler import (
    show_ams,
    show_customer_menu,
    show_customers,
)

from app.handlers.tunggakan_handler import show_tunggakan
from app.handlers.invoice_handler import show_invoice


async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    print(f"[CALLBACK] {data}")

    # =========================================================
    # AUTH CALLBACK
    # =========================================================

    if (
        data.startswith("auth_approve:")
        or data.startswith("auth_reject:")
    ):
        await handle_auth_callback(
            query,
            context,
        )
        return

    # =========================================================
    # ADMIN CALLBACK
    # =========================================================

    if (
        data == "admin_dashboard"
        or data == "admin_refresh"
        or data == "admin_noop"
        or data.startswith("admin_users:")
        or data.startswith("admin_user:")
        or data.startswith("admin_approve:")
        or data.startswith("admin_reject:")
    ):
        await handle_admin_callback(
            query,
            context,
        )
        return

    # =========================================================
    # ANSWER CALLBACK
    # =========================================================

    try:
        await query.answer()
    except Exception:
        pass

    # =========================================================
    # NOOP
    # =========================================================

    if data == "noop":
        return

    # =========================================================
    # COMMAND CUSTOMER
    #
    # Contoh:
    # command_customer:cyc:4806453
    # command_customer:saldo_cr:4807121
    # command_customer:invoice:4807121
    # =========================================================

    if data.startswith("command_customer:"):
        parts = data.split(":", 2)

        if len(parts) != 3:
            print(
                "[CALLBACK ERROR] "
                f"Format command_customer tidak valid: {data}"
            )
            return

        command = parts[1].strip()
        customer_id = parts[2].strip()

        print(
            "[COMMAND CUSTOMER] "
            f"Command = {command} | ID = {customer_id}"
        )

        if not customer_id:
            print(
                "[CALLBACK ERROR] "
                "Customer ID kosong."
            )
            return

        context.user_data[
            "selected_customer_id"
        ] = customer_id

        # Simpan pesan list sebelum diubah menjadi detail.
        save_customer_list_message(
            query,
            context,
        )

        prepare_detail_message(
            query,
            context,
        )

        # -----------------------------------------------------
        # TUNGGAKAN
        # -----------------------------------------------------

        if command == "tunggakan":
            context.user_data[
                "active_menu"
            ] = "tunggakan"

            await show_tunggakan(
                query,
                context,
            )
            return

        # -----------------------------------------------------
        # INVOICE
        # -----------------------------------------------------

        if command == "invoice":
            context.user_data[
                "active_menu"
            ] = "invoice"

            await show_invoice(
                query,
                context,
            )
            return

        # -----------------------------------------------------
        # SALDO CYC
        # -----------------------------------------------------

        if command == "cyc":
            context.user_data[
                "active_menu"
            ] = "pelanggan_tunggakan"

            await show_tunggakan(
                query,
                context,
            )
            return

        # -----------------------------------------------------
        # SALDO CR
        # -----------------------------------------------------

        if command == "saldo_cr":
            context.user_data[
                "active_menu"
            ] = "saldo_cr"

            await show_tunggakan(
                query,
                context,
            )
            return

        # -----------------------------------------------------
        # CUSTOMER
        # -----------------------------------------------------

        if command == "customer":
            context.user_data[
                "active_menu"
            ] = "customer"

            await show_customer_info(
                query,
                context,
            )
            return

        print(
            "[CALLBACK ERROR] "
            f"Command tidak dikenal: {command}"
        )

        return

    # =========================================================
    # SELECT AM
    # =========================================================

    if data.startswith("select_am:"):
        am_name = (
            data
            .split(":", 1)[1]
            .strip()
        )

        print(
            f"[AM DIPILIH] {am_name}"
        )

        context.user_data[
            "current_am"
        ] = am_name

        context.user_data[
            "active_menu"
        ] = None

        context.user_data[
            "customer_page"
        ] = 0

        context.user_data[
            "selected_customer_id"
        ] = None

        context.user_data.pop(
            "search_mode",
            None,
        )

        clear_detail_state(
            context
        )

        await show_customer_menu(
            update,
            context,
        )

        return

    # =========================================================
    # AM PAGE
    # =========================================================

    if data.startswith("am_page:"):
        try:
            page = int(
                data
                .split(":", 1)[1]
            )
        except (
            ValueError,
            IndexError,
        ):
            page = 0

        print(
            f"[AM PAGE] {page}"
        )

        await show_ams(
            update,
            context,
            page=page,
        )

        return

    # =========================================================
    # BACK TO AM LIST
    # =========================================================

    if data == "back_to_ams":
        print(
            "[NAVIGATION] "
            "Kembali ke daftar AM"
        )

        context.user_data[
            "current_am"
        ] = None

        context.user_data[
            "active_menu"
        ] = None

        context.user_data[
            "customer_page"
        ] = 0

        context.user_data[
            "selected_customer_id"
        ] = None

        context.user_data.pop(
            "search_mode",
            None,
        )

        clear_detail_state(
            context
        )

        await show_ams(
            update,
            context,
            page=0,
        )

        return

    # =========================================================
    # AM MENU
    # =========================================================

    if data.startswith("am_menu:"):
        menu = (
            data
            .split(":", 1)[1]
            .strip()
        )

        if menu not in (
            "pelanggan_tunggakan",
            "invoice",
            "tunggakan",
            "saldo_cr",
        ):
            print(
                "[CALLBACK ERROR] "
                f"Menu AM tidak valid: {menu}"
            )
            return

        print(
            f"[AM MENU] {menu}"
        )

        context.user_data[
            "active_menu"
        ] = menu

        context.user_data[
            "customer_page"
        ] = 0

        context.user_data[
            "selected_customer_id"
        ] = None

        context.user_data.pop(
            "search_mode",
            None,
        )

        clear_detail_state(
            context
        )

        await show_customers(
            update,
            context,
            page=0,
        )

        return

    # =========================================================
    # CUSTOMER MENU
    # =========================================================

    if data.startswith("customer_menu:"):
        menu = (
            data
            .split(":", 1)[1]
            .strip()
        )

        if menu not in (
            "pelanggan_tunggakan",
            "invoice",
            "tunggakan",
            "saldo_cr",
        ):
            print(
                "[CALLBACK ERROR] "
                f"Menu customer tidak valid: {menu}"
            )
            return

        print(
            f"[CUSTOMER MENU] {menu}"
        )

        context.user_data[
            "active_menu"
        ] = menu

        context.user_data[
            "customer_page"
        ] = 0

        context.user_data[
            "selected_customer_id"
        ] = None

        context.user_data.pop(
            "search_mode",
            None,
        )

        clear_detail_state(
            context
        )

        await show_customers(
            update,
            context,
            page=0,
        )

        return

    # =========================================================
    # CUSTOMER PAGE
    # =========================================================

    if data.startswith("customer_page:"):
        try:
            page = int(
                data
                .split(":", 1)[1]
            )
        except (
            ValueError,
            IndexError,
        ):
            page = 0

        print(
            f"[CUSTOMER PAGE] {page}"
        )

        context.user_data[
            "customer_page"
        ] = page

        context.user_data[
            "selected_customer_id"
        ] = None

        context.user_data.pop(
            "search_mode",
            None,
        )

        clear_detail_state(
            context
        )

        await show_customers(
            update,
            context,
            page=page,
        )

        return

    # =========================================================
    # CUSTOMER SELECT
    # =========================================================

    if data.startswith("customer_select:"):
        customer_id = (
            data
            .split(":", 1)[1]
            .strip()
        )

        print(
            f"[CUSTOMER DIPILIH] {customer_id}"
        )

        if not customer_id:
            print(
                "[CALLBACK ERROR] "
                "Customer ID kosong."
            )
            return

        # Simpan pesan list sebelum diubah menjadi detail.
        save_customer_list_message(
            query,
            context,
        )

        context.user_data[
            "selected_customer_id"
        ] = customer_id

        active_menu = (
            context.user_data.get(
                "active_menu"
            )
        )

        print(
            "[CUSTOMER CONTEXT] "
            f"Active menu = {active_menu} | "
            f"ID = {customer_id}"
        )

        prepare_detail_message(
            query,
            context,
        )

        # -----------------------------------------------------
        # INVOICE
        # -----------------------------------------------------

        if active_menu == "invoice":
            print(
                f"[INVOICE] ID = {customer_id}"
            )

            await show_invoice(
                query,
                context,
            )

            return

        # -----------------------------------------------------
        # SALDO CYC
        # -----------------------------------------------------

        if active_menu in (
            "tunggakan",
            "pelanggan_tunggakan",
        ):
            print(
                f"[SALDO CYC] ID = {customer_id}"
            )

            await show_tunggakan(
                query,
                context,
            )

            return

        # -----------------------------------------------------
        # SALDO CR
        # -----------------------------------------------------

        if active_menu == "saldo_cr":
            print(
                f"[SALDO CR] ID = {customer_id}"
            )

            await show_tunggakan(
                query,
                context,
            )

            return

        # -----------------------------------------------------
        # CUSTOMER
        # -----------------------------------------------------

        if active_menu == "customer":
            await show_customer_info(
                query,
                context,
            )
            return

        print(
            "[CALLBACK ERROR] "
            "Active menu tidak tersedia."
        )

        return

    # =========================================================
    # BACK TO CUSTOMER LIST
    #
    # INI BAGIAN YANG DIPERBAIKI
    # =========================================================

    if data in (
        "close_detail",
        "back_to_customer_list",
        "back_to_customers",
    ):
        print(
            "[NAVIGATION] "
            "Kembali ke customer list"
        )

        context.user_data[
            "selected_customer_id"
        ] = None

        clear_detail_state(
            context
        )

        # PENTING:
        # Kirim objek Update asli, bukan CallbackQuery.
        await restore_customer_list(
            update,
            context,
        )

        return

    # =========================================================
    # BACK TO CUSTOMER MENU
    # =========================================================

    if data == "back_to_customer_menu":
        print(
            "[NAVIGATION] "
            "Kembali ke menu AM"
        )

        context.user_data[
            "customer_page"
        ] = 0

        context.user_data[
            "selected_customer_id"
        ] = None

        context.user_data[
            "active_menu"
        ] = None

        context.user_data.pop(
            "search_mode",
            None,
        )

        clear_detail_state(
            context
        )

        await show_customer_menu(
            update,
            context,
        )

        return

    # =========================================================
    # SEARCH AM
    # =========================================================

    if data == "search_am":
        print(
            "[SEARCH] Mode pencarian AM"
        )

        context.user_data[
            "search_mode"
        ] = "am"

        try:
            await query.edit_message_text(
                text=(
                    "CARI AM\n\n"
                    "Silakan masukkan nama AM "
                    "yang ingin dicari."
                )
            )
        except Exception as error:
            if "Message is not modified" in str(error):
                pass
            else:
                print(
                    f"[SEARCH AM ERROR] {error}"
                )

        return

    # =========================================================
    # SEARCH CUSTOMER
    # =========================================================

    if data == "search_customer":
        print(
            "[SEARCH] Mode pencarian customer"
        )

        context.user_data[
            "search_mode"
        ] = "customer"

        try:
            await query.edit_message_text(
                text=(
                    "CARI CUSTOMER\n\n"
                    "Silakan masukkan nama perusahaan "
                    "atau ID pelanggan."
                )
            )
        except Exception as error:
            if "Message is not modified" in str(error):
                pass
            else:
                print(
                    f"[SEARCH CUSTOMER ERROR] {error}"
                )

        return

    # =========================================================
    # UNKNOWN CALLBACK
    # =========================================================

    print(
        "[WARNING] "
        f"Callback tidak dikenal: {data}"
    )


# =========================================================
# SHOW CUSTOMER INFO
# =========================================================

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

    from app.services.customer_service import (
        CustomerService,
    )

    customer_service = CustomerService()

    customers = (
        customer_service
        .get_all_customers()
    )

    target_customer = None

    target_id = normalize_customer_id(
        customer_id
    )

    for customer in customers:
        customer_id_value = (
            customer.get("idnumber")
            or customer.get("ID")
            or customer.get("id")
        )

        normalized_id = (
            normalize_customer_id(
                customer_id_value
            )
        )

        if not normalized_id:
            continue

        if normalized_id == target_id:
            target_customer = customer
            break

    if not target_customer:
        print(
            "[CUSTOMER INFO ERROR] "
            f"Customer {customer_id} tidak ditemukan."
        )
        return

    pelanggan = (
        target_customer.get("PELANGGAN")
        or target_customer.get("nama")
        or target_customer.get("CUSTOMER")
        or target_customer.get("pcTCYC")
        or "-"
    )

    am = (
        target_customer.get("AM")
        or target_customer.get("am")
        or "-"
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

        print(
            "[CUSTOMER INFO] "
            "Detail ditampilkan pada pesan yang sama."
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
        if "Message is not modified" in str(error):
            print(
                "[CUSTOMER INFO] "
                "Pesan sudah dalam kondisi yang sama."
            )
        else:
            print(
                f"[CUSTOMER INFO ERROR] {error}"
            )


# =========================================================
# RESTORE CUSTOMER LIST
# =========================================================

async def restore_customer_list(
    update: Update,
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

    page = (
        context.user_data.get(
            "customer_page",
            0,
        )
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
        # =====================================================
        # PERBAIKAN UTAMA:
        # gunakan Update asli dari callback_handler
        # =====================================================

        await show_customers(
            update=update,
            context=context,
            page=page,
            message_id=list_message_id,
            chat_id=list_chat_id,
        )

        print(
            "[LIST] "
            "Customer list dikembalikan "
            "pada pesan yang sama."
        )

    except Exception as error:
        if "Message is not modified" in str(error):
            print(
                "[LIST] "
                "Customer list sudah dalam kondisi "
                "yang sama."
            )
        else:
            print(
                f"[RESTORE LIST ERROR] {error}"
            )


# =========================================================
# SAVE CUSTOMER LIST MESSAGE
# =========================================================

def save_customer_list_message(
    query,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not query.message:
        return

    context.user_data[
        "customer_list_message_id"
    ] = query.message.message_id

    context.user_data[
        "customer_list_chat_id"
    ] = query.message.chat_id


# =========================================================
# PREPARE DETAIL MESSAGE
# =========================================================

def prepare_detail_message(
    query,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not query.message:
        return

    context.user_data[
        "detail_message_id"
    ] = query.message.message_id

    context.user_data[
        "detail_chat_id"
    ] = query.message.chat_id


# =========================================================
# NORMALIZE CUSTOMER ID
# =========================================================

def normalize_customer_id(
    value,
):
    if value is None:
        return ""

    text = str(value).strip()

    if not text:
        return ""

    if text.endswith(".0"):
        try:
            number = float(text)

            if number.is_integer():
                return str(
                    int(number)
                )

        except (
            ValueError,
            TypeError,
        ):
            pass

    try:
        number = float(text)

        if number.is_integer():
            return str(
                int(number)
            )

    except (
        ValueError,
        TypeError,
    ):
        pass

    return text


# =========================================================
# CLEAR DETAIL STATE
# =========================================================

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