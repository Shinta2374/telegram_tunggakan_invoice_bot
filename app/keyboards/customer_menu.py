from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_customer_menu(
    customers,
    page=0,
    per_page=5
):

    start = page * per_page
    end = start + per_page

    page_customers = customers[start:end]

    keyboard = []

    for customer in page_customers:

        nama = str(
            customer.get("NAMA", "-")
        ).strip()

        idnumber = str(
            customer.get("idnumber", "-")
        ).strip()

        # Batasi panjang nama agar keyboard tetap rapi
        if len(nama) > 28:
            nama_display = nama[:25] + "..."
        else:
            nama_display = nama

        keyboard.append([
            InlineKeyboardButton(
                f"{nama_display}",
                callback_data=f"tunggakan:{idnumber}"
            ),
            InlineKeyboardButton(
                "Invoice",
                callback_data=f"invoice:{idnumber}"
            )
        ])

    # PAGINATION

    total_pages = max(
        1,
        (len(customers) + per_page - 1) // per_page
    )

    navigation = []

    if page > 0:

        navigation.append(
            InlineKeyboardButton(
                "Sebelumnya",
                callback_data=f"customer_page:{page - 1}"
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"{page + 1}/{total_pages}",
            callback_data="noop"
        )
    )

    if end < len(customers):

        navigation.append(
            InlineKeyboardButton(
                "Selanjutnya",
                callback_data=f"customer_page:{page + 1}"
            )
        )

    keyboard.append(navigation)

    # SEARCH

    keyboard.append([
        InlineKeyboardButton(
            "Cari Customer",
            callback_data="search_customer"
        )
    ])

    # =========================
    # BACK
    # =========================

    keyboard.append([
        InlineKeyboardButton(
            "Kembali ke AM",
            callback_data="back_to_am"
        )
    ])

    return InlineKeyboardMarkup(keyboard)