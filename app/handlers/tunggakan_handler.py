from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from app.services.tunggakan_service import TunggakanService


tunggakan_service = TunggakanService()


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

        month = periode[4:6]

        return MONTH_NAMES.get(
            month,
            periode,
        )

    return periode


def build_tunggakan_text(result):

    pelanggan = (
        normalize(
            result.get("PELANGGAN")
        )
        or "-"
    )

    idnumber = (
        normalize(
            result.get("idnumber")
        )
        or "-"
    )

    am = (
        normalize(
            result.get("am")
        )
        or "-"
    )

    saldo = result.get(
        "saldo_akhir_cyc",
        0,
    )

    text = (
        "INFORMASI TUNGGAKAN\n\n"
        f"{pelanggan} ({idnumber})\n"
        f"{am}\n"
    )

    # =========================================================
    # AGING TUNGGAKAN
    # =========================================================

    aging = result.get(
        "aging",
        [],
    )

    if aging:

        aging_lines = []

        for item in aging:

            periode = normalize(
                item.get("periode")
            )

            nominal = item.get(
                "nominal",
                0,
            )

            if not nominal:
                continue

            aging_lines.append(
                f"{periode}: "
                f"{format_rupiah(nominal)}"
            )

        if aging_lines:

            text += (
                "\n"
                "────────────────────────────\n"
                "AGING TUNGGAKAN\n"
            )

            for line in aging_lines:

                text += (
                    f"{line}\n"
                )

    # =========================================================
    # TUNGGAKAN 2026
    # =========================================================

    tunggakan_periode = result.get(
        "tunggakan_periode",
        [],
    )

    text += (
        "\n"
        "────────────────────────────\n"
        "TUNGGAKAN 2026\n"
    )

    if tunggakan_periode:

        periode_lines = []

        for item in tunggakan_periode:

            periode = format_periode(
                item.get("periode")
            )

            nominal = item.get(
                "nominal",
                0,
            )

            if not nominal:
                continue

            periode_lines.append(
                f"• {periode}: "
                f"{format_rupiah(nominal)}"
            )

        if periode_lines:

            for line in periode_lines:

                text += (
                    f"{line}\n"
                )

        else:

            text += (
                "Tidak ada tunggakan "
                "pada periode berjalan.\n"
            )

    else:

        text += (
            "Tidak ada tunggakan "
            "pada periode berjalan.\n"
        )

    # =========================================================
    # TOTAL CYC
    # =========================================================

    text += (
        "\n"
        "────────────────────────────\n"
        "TOTAL CYC\n"
        f"{format_rupiah(saldo)}\n"
    )

    return text


async def show_tunggakan(
    query,
    context: ContextTypes.DEFAULT_TYPE,
):
    customer_id = context.user_data.get(
        "selected_customer_id"
    )

    print(
        f"[SHOW TUNGGAKAN] ID = {customer_id}"
    )

    if not customer_id:

        await query.message.reply_text(
            "ID Pelanggan belum tersedia."
        )

        return

    try:

        result = (
            tunggakan_service
            .get_tunggakan(
                customer_id
            )
        )

        print(
            "[SHOW TUNGGAKAN] "
            f"RESULT = {result}"
        )

        if not result:

            await query.message.reply_text(
                "Data tunggakan tidak ditemukan."
            )

            return

        text = build_tunggakan_text(
            result
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Kembali ke Customer",
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

        # =====================================================
        # EDIT DETAIL MESSAGE YANG SUDAH ADA
        # =====================================================

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
                ] = "tunggakan"

                return

            except Exception as e:

                print(
                    "[DETAIL EDIT ERROR] "
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

                context.user_data.pop(
                    "detail_type",
                    None,
                )

        # =====================================================
        # BUAT DETAIL MESSAGE BARU
        # =====================================================

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
        ] = "tunggakan"

    except Exception as e:

        print(
            "======================================"
        )

        print(
            "[TUNGGAKAN ERROR]"
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
            f"Error       : {e}"
        )

        print(
            "======================================"
        )

        await query.message.reply_text(
            "Terjadi kesalahan saat "
            "mengambil data tunggakan."
        )


async def show_tunggakan_from_update(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    await show_tunggakan(
        query,
        context,
    )