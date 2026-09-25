from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from app.services.tunggakan_service import (
    TunggakanService,
)


SEPARATOR = "────────────"


def normalize(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def format_rupiah(value):
    try:
        value = float(value or 0)
    except (
        ValueError,
        TypeError,
    ):
        value = 0

    return (
        "Rp "
        + f"{value:,.0f}".replace(
            ",",
            ".",
        )
    )


def format_periode(value):
    periode_map = {
        "202601": "Januari 2026",
        "202602": "Februari 2026",
        "202603": "Maret 2026",
        "202604": "April 2026",
        "202605": "Mei 2026",
        "202606": "Juni 2026",
        "202607": "Juli 2026",
        "202608": "Agustus 2026",
        "202609": "September 2026",
        "202610": "Oktober 2026",
        "202611": "November 2026",
        "202612": "Desember 2026",
    }

    return periode_map.get(
        str(value),
        str(value),
    )


def build_tunggakan_text(result):
    if not result:
        return "Data Tunggakan tidak ditemukan."

    pelanggan = result.get(
        "PELANGGAN",
        "-",
    )

    idnumber = result.get(
        "idnumber",
        "-",
    )

    am = result.get(
        "am",
        "-",
    )

    saldo_akhir_cyc = result.get(
        "saldo_akhir_cyc",
        0,
    )

    aging = result.get(
        "aging",
        [],
    )

    tunggakan_periode = result.get(
        "tunggakan_periode",
        [],
    )

    lines = [
        "INFORMASI TUNGGAKAN",
        "",
        f"{pelanggan} ({idnumber})",
        f"AM: {am}",
    ]

    if aging:
        lines.extend(
            [
                "",
                "AGING TUNGGAKAN",
                SEPARATOR,
            ]
        )

        for item in aging:
            periode = item.get(
                "periode",
                "-",
            )

            nominal = item.get(
                "nominal",
                0,
            )

            lines.append(
                f"{periode}: "
                f"{format_rupiah(nominal)}"
            )

    if tunggakan_periode:
        lines.extend(
            [
                "",
                "TUNGGAKAN 2026",
                SEPARATOR,
            ]
        )

        for item in tunggakan_periode:
            periode = format_periode(
                item.get("periode")
            )

            nominal = item.get(
                "nominal",
                0,
            )

            lines.append(
                f"{periode}: "
                f"{format_rupiah(nominal)}"
            )

    lines.extend(
        [
            "",
            "TOTAL CYC",
            SEPARATOR,
            format_rupiah(
                saldo_akhir_cyc
            ),
        ]
    )

    return "\n".join(lines)


def build_saldo_cyc_text(result):
    if not result:
        return "Data Saldo CYC tidak ditemukan."

    pelanggan = result.get(
        "PELANGGAN",
        "-",
    )

    idnumber = result.get(
        "idnumber",
        "-",
    )

    am = result.get(
        "am",
        "-",
    )

    saldo_cyc_periode = result.get(
        "saldo_cyc_periode",
        [],
    )

    total_cyc = result.get(
        "saldo_akhir_cyc",
        0,
    )

    saldo_cr = result.get(
        "saldo_akhir",
        0,
    )

    lines = [
        "INFORMASI SALDO CYC",
        "",
        f"{pelanggan} ({idnumber})",
        f"AM: {am}",
    ]

    non_zero_periods = []

    for item in saldo_cyc_periode:
        nominal = item.get(
            "nominal",
            0,
        )

        try:
            nominal = float(
                nominal or 0
            )
        except (
            ValueError,
            TypeError,
        ):
            nominal = 0

        if nominal != 0:
            non_zero_periods.append(
                {
                    "periode": item.get(
                        "periode"
                    ),
                    "nominal": nominal,
                }
            )

    if non_zero_periods:
        lines.extend(
            [
                "",
                "SALDO CYC",
                SEPARATOR,
            ]
        )

        for item in non_zero_periods:
            periode = format_periode(
                item.get("periode")
            )

            nominal = item.get(
                "nominal",
                0,
            )

            lines.append(
                f"{periode}: "
                f"{format_rupiah(nominal)}"
            )

    lines.extend(
        [
            "",
            "TOTAL CYC",
            SEPARATOR,
            format_rupiah(
                total_cyc
            ),
        ]
    )

    lines.extend(
        [
            "",
            "SALDO CR",
            SEPARATOR,
            format_rupiah(
                saldo_cr
            ),
        ]
    )

    return "\n".join(lines)


def build_saldo_cr_text(result):
    if not result:
        return "Data Saldo CR tidak ditemukan."

    pelanggan = result.get(
        "PELANGGAN",
        "-",
    )

    idnumber = result.get(
        "idnumber",
        "-",
    )

    am = result.get(
        "am",
        "-",
    )

    saldo_cr = result.get(
        "saldo_akhir",
        0,
    )

    saldo_cyc = result.get(
        "saldo_akhir_cyc",
        0,
    )

    aging = result.get(
        "aging",
        [],
    )

    lines = [
        "INFORMASI SALDO CR",
        "",
        f"{pelanggan} ({idnumber})",
        f"AM: {am}",
    ]

    lines.extend(
        [
            "",
            "SALDO CR",
            SEPARATOR,
            f"Saldo Akhir: "
            f"{format_rupiah(saldo_cr)}",
        ]
    )

    lines.extend(
        [
            "",
            "SALDO CYC",
            SEPARATOR,
            format_rupiah(
                saldo_cyc
            ),
        ]
    )

    non_zero_aging = []

    for item in aging:
        nominal = item.get(
            "nominal",
            0,
        )

        try:
            nominal = float(
                nominal or 0
            )
        except (
            ValueError,
            TypeError,
        ):
            nominal = 0

        if nominal != 0:
            non_zero_aging.append(
                {
                    "periode": item.get(
                        "periode"
                    ),
                    "nominal": nominal,
                }
            )

    if non_zero_aging:
        lines.extend(
            [
                "",
                "AGING SALDO CR",
                SEPARATOR,
            ]
        )

        for item in non_zero_aging:
            periode = item.get(
                "periode",
                "-",
            )

            nominal = item.get(
                "nominal",
                0,
            )

            lines.append(
                f"{periode}: "
                f"{format_rupiah(nominal)}"
            )

    return "\n".join(lines)


async def show_tunggakan(
    query,
    context,
):
    customer_id = (
        context.user_data.get(
            "selected_customer_id"
        )
    )

    if not customer_id:
        print(
            "[SALDO ERROR] "
            "Customer ID belum tersedia."
        )
        return

    active_menu = (
        context.user_data.get(
            "active_menu"
        )
    )

    tunggakan_service = (
        TunggakanService()
    )

    result = None
    text = ""
    detail_type = ""

    if active_menu == "saldo_cr":
        print(
            "[SALDO CR] "
            f"Mengambil detail ID = "
            f"{customer_id}"
        )

        result = (
            tunggakan_service
            .get_saldo_cr(
                customer_id
            )
        )

        text = build_saldo_cr_text(
            result
        )

        detail_type = "saldo_cr"

    elif active_menu in (
        "pelanggan_tunggakan",
        "cyc",
    ):
        print(
            "[SALDO CYC] "
            f"Mengambil detail ID = "
            f"{customer_id}"
        )

        result = (
            tunggakan_service
            .get_saldo_cyc(
                customer_id
            )
        )

        text = build_saldo_cyc_text(
            result
        )

        detail_type = "saldo_cyc"

    else:
        print(
            "[TUNGGAKAN] "
            f"Mengambil detail ID = "
            f"{customer_id}"
        )

        result = (
            tunggakan_service
            .get_tunggakan(
                customer_id
            )
        )

        text = build_tunggakan_text(
            result
        )

        detail_type = "tunggakan"

    if result is None:
        text = (
            "DATA TIDAK DITEMUKAN\n\n"
            f"Customer ID: {customer_id}"
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
        ] = detail_type

        print(
            "[SALDO] "
            "Detail berhasil ditampilkan."
        )

    except Exception as error:
        if (
            "Message is not modified"
            in str(error)
        ):
            print(
                "[SALDO] "
                "Pesan sudah dalam kondisi "
                "yang sama."
            )
        else:
            print(
                f"[SALDO ERROR] {error}"
            )


async def show_tunggakan_from_update(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return

    await show_tunggakan(
        query,
        context,
    )