from telegram import Update
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

    if (
        data.startswith("auth_approve:")
        or data.startswith("auth_reject:")
    ):
        await handle_auth_callback(
            query,
            context,
        )
        return

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

    await query.answer()

    if data == "noop":
        return

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
            f"[COMMAND CUSTOMER] "
            f"Command = {command} | ID = {customer_id}"
        )

        if not customer_id:
            print("[CALLBACK ERROR] Customer ID kosong.")
            return

        context.user_data["selected_customer_id"] = customer_id

        if query.message:
            context.user_data[
                "customer_list_message_id"
            ] = query.message.message_id

            context.user_data[
                "customer_list_chat_id"
            ] = query.message.chat_id

        if command == "tunggakan":
            context.user_data["active_menu"] = "tunggakan"

            await show_tunggakan(
                query,
                context,
            )
            return

        if command == "invoice":
            context.user_data["active_menu"] = "invoice"

            await show_invoice(
                query,
                context,
            )
            return

        if command == "cyc":
            context.user_data["active_menu"] = "cyc"

            await show_tunggakan(
                query,
                context,
            )
            return

        if command == "customer":
            context.user_data["active_menu"] = "customer"

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

    if data.startswith("select_am:"):
        am_name = (
            data
            .split(":", 1)[1]
            .strip()
        )

        print(f"[AM DIPILIH] {am_name}")

        context.user_data["current_am"] = am_name
        context.user_data["active_menu"] = None
        context.user_data["customer_page"] = 0
        context.user_data["selected_customer_id"] = None

        clear_detail_state(context)

        await show_customer_menu(
            update,
            context,
        )

        return

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

        await show_ams(
            update,
            context,
            page=page,
        )

        return

    if data == "back_to_ams":
        await delete_detail_message(
            query,
            context,
        )

        context.user_data["current_am"] = None
        context.user_data["active_menu"] = None
        context.user_data["customer_page"] = 0
        context.user_data["selected_customer_id"] = None

        clear_detail_state(context)

        await show_ams(
            update,
            context,
            page=0,
        )

        return

    if data.startswith("customer_menu:"):
        menu = (
            data
            .split(":", 1)[1]
            .strip()
        )

        if menu not in (
            "invoice",
            "tunggakan",
            "pelanggan_tunggakan",
        ):
            print(
                "[CALLBACK ERROR] "
                f"Menu tidak valid: {menu}"
            )
            return

        print(f"[MENU DIPILIH] {menu}")

        context.user_data["active_menu"] = menu
        context.user_data["customer_page"] = 0
        context.user_data["selected_customer_id"] = None

        clear_detail_state(context)

        await show_customers(
            update,
            context,
            page=0,
        )

        return

    if data.startswith("am_menu:"):
        menu = (
            data
            .split(":", 1)[1]
            .strip()
        )

        if menu not in (
            "invoice",
            "tunggakan",
            "pelanggan_tunggakan",
        ):
            print(
                "[CALLBACK ERROR] "
                f"Menu tidak valid: {menu}"
            )
            return

        context.user_data["active_menu"] = menu
        context.user_data["customer_page"] = 0
        context.user_data["selected_customer_id"] = None

        clear_detail_state(context)

        await show_customers(
            update,
            context,
            page=0,
        )

        return

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

        context.user_data["customer_page"] = page
        context.user_data["selected_customer_id"] = None

        clear_detail_state(context)

        await show_customers(
            update,
            context,
            page=page,
        )

        return

    if data.startswith("customer_select:"):
        customer_id = (
            data
            .split(":", 1)[1]
            .strip()
        )

        print(
            f"[CUSTOMER DIPILIH] {customer_id}"
        )

        if query.message:
            context.user_data[
                "customer_list_message_id"
            ] = query.message.message_id

            context.user_data[
                "customer_list_chat_id"
            ] = query.message.chat_id

        context.user_data[
            "selected_customer_id"
        ] = customer_id

        active_menu = context.user_data.get(
            "active_menu"
        )

        if active_menu == "invoice":
            print(
                f"[INVOICE] ID = {customer_id}"
            )

            await show_invoice(
                query,
                context,
            )

            return

        if active_menu in (
            "tunggakan",
            "pelanggan_tunggakan",
        ):
            print(
                f"[TUNGGAKAN] ID = {customer_id}"
            )

            await show_tunggakan(
                query,
                context,
            )

            return

        print(
            "[CALLBACK ERROR] "
            "Active menu tidak tersedia."
        )

        return

    if data in (
        "close_detail",
        "back_to_customer_list",
        "back_to_customers",
    ):
        await delete_detail_message(
            query,
            context,
        )

        context.user_data[
            "selected_customer_id"
        ] = None

        clear_detail_state(context)

        await restore_customer_list(
            query,
            context,
        )

        return

    if data == "back_to_customer_menu":
        context.user_data["customer_page"] = 0
        context.user_data["selected_customer_id"] = None
        context.user_data["active_menu"] = None

        clear_detail_state(context)

        await show_customer_menu(
            update,
            context,
        )

        return

    if data == "search_am":
        context.user_data["search_mode"] = "am"

        await query.message.reply_text(
            "Silakan masukkan nama AM "
            "yang ingin dicari."
        )

        return

    if data == "search_customer":
        context.user_data["search_mode"] = "customer"

        await query.message.reply_text(
            "Silakan masukkan nama perusahaan "
            "atau ID pelanggan."
        )

        return

    print(
        "[WARNING] "
        f"Callback tidak dikenal: {data}"
    )


async def show_customer_info(
    query,
    context: ContextTypes.DEFAULT_TYPE,
):
    customer_id = context.user_data.get(
        "selected_customer_id"
    )

    if not customer_id:
        await query.message.reply_text(
            "ID Pelanggan belum tersedia."
        )
        return

    from app.services.customer_service import CustomerService

    customer_service = CustomerService()

    customers = customer_service.get_all_customers()

    target_customer = None

    for customer in customers:
        customer_id_value = (
            customer.get("idnumber")
            or customer.get("ID")
            or customer.get("id")
        )

        if customer_id_value is None:
            continue

        normalized_id = str(
            customer_id_value
        ).strip()

        if normalized_id.endswith(".0"):
            normalized_id = normalized_id[:-2]

        if normalized_id == str(
            customer_id
        ).strip():
            target_customer = customer
            break

    if not target_customer:
        await query.message.reply_text(
            "Data pelanggan tidak ditemukan."
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
        f"{pelanggan} ({customer_id})\n"
        f"{am}"
    )

    await query.message.reply_text(text)


async def delete_detail_message(
    query,
    context: ContextTypes.DEFAULT_TYPE,
):
    detail_message_id = context.user_data.get(
        "detail_message_id"
    )

    detail_chat_id = context.user_data.get(
        "detail_chat_id"
    )

    if not detail_message_id or not detail_chat_id:
        return

    try:
        await query.get_bot().delete_message(
            chat_id=detail_chat_id,
            message_id=detail_message_id,
        )

        print("[DETAIL] Pesan detail dihapus.")

    except Exception as error:
        print(
            f"[DELETE DETAIL ERROR] {error}"
        )


async def restore_customer_list(
    query,
    context: ContextTypes.DEFAULT_TYPE,
):
    list_message_id = context.user_data.get(
        "customer_list_message_id"
    )

    list_chat_id = context.user_data.get(
        "customer_list_chat_id"
    )

    page = context.user_data.get(
        "customer_page",
        0,
    )

    if not list_message_id:
        print(
            "[LIST] ID pesan list tidak ditemukan."
        )
        return

    if not list_chat_id:
        print(
            "[LIST] Chat ID list tidak ditemukan."
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

        print("[LIST] List customer dikembalikan.")

    except Exception as error:
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