"""
Handler untuk menampilkan informasi tunggakan customer.
"""

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from app.services.tunggakan_service import (
    TunggakanService,
)


tunggakan_service = TunggakanService()


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


def build_tunggakan_text(result):

    PELANGGAN = (
        normalize(result.get("PELANGGAN"))
        or "-"
    )

    idnumber = (
        normalize(result.get("idnumber"))
        or "-"
    )

    am = (
        normalize(result.get("am"))
        or "-"
    )

    saldo = result.get(
        "saldo_akhir_cyc",
        0
    )

    text = (
        "📄 INFORMASI TUNGGAKAN\n\n"
        f"🏢 {PELANGGAN}\n"
        f"🆔 `{idnumber}`\n"
        f"👤 {am}\n\n"
        f"💰 **Saldo Akhir CYC:** "
        f"{format_rupiah(saldo)}\n"
    )

    aging = result.get(
        "aging",
        []
    )

    if aging:

        text += "\n**AGING TUNGGAKAN**\n"

        for item in aging:

            periode = normalize(
                item.get("periode")
            )

            nominal = item.get(
                "nominal",
                0
            )

            if not nominal:
                continue

            text += (
                f"• {periode}: "
                f"{format_rupiah(nominal)}\n"
            )

    tunggakan_periode = result.get(
        "tunggakan_periode",
        []
    )

    if tunggakan_periode:

        text += (
            "\n"
            "**PERIODE YANG MASIH MEMILIKI "
            "TUNGGAKAN**\n"
        )

        for item in tunggakan_periode:

            periode = normalize(
                item.get("periode")
            )

            nominal = item.get(
                "nominal",
                0
            )

            if not nominal:
                continue

            text += (
                f"• {periode}: "
                f"{format_rupiah(nominal)}\n"
            )

    else:

        text += (
            "\n"
            "**PERIODE YANG MASIH MEMILIKI "
            "TUNGGAKAN**\n"
            "Tidak ada tunggakan "
            "pada periode berjalan."
        )

    return text


async def show_tunggakan(
    query,
    context,
):

    customer_id = context.user_data.get(
        "selected_customer_id"
    )

    print(
        f"[SHOW TUNGGAKAN] ID = {customer_id}"
    )

    if not customer_id:

        await query.message.reply_text(
            "❌ ID Pelanggan belum tersedia."
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
            f"[SHOW TUNGGAKAN] RESULT = {result}"
        )

        if not result:

            await query.message.reply_text(
                "❌ Data tunggakan tidak ditemukan."
            )

            return

        text = build_tunggakan_text(
            result
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Kembali ke Customer",
                    callback_data="close_detail"
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
            and detail_chat_id == current_chat_id
        ):

            try:

                await query.get_bot().edit_message_text(
                    chat_id=detail_chat_id,
                    message_id=detail_message_id,
                    text=text,
                    reply_markup=markup,
                    parse_mode="Markdown",
                )

                context.user_data[
                    "detail_type"
                ] = "tunggakan"

                return

            except Exception as e:

                print(
                    f"[DETAIL EDIT ERROR] {e}"
                )

        message = (
            await query.message.reply_text(
                text=text,
                reply_markup=markup,
                parse_mode="Markdown",
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
            "======================================"
        )

        await query.message.reply_text(
            "❌ Terjadi kesalahan saat "
            "mengambil data tunggakan."
        )