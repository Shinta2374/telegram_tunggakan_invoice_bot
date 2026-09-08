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
        )

        am = str(
            customer.get("AM", "-")
        )

        idnumber = str(
            customer.get("idnumber", "-")
        )

        # Batasi nama
        if len(nama) > 20:
            nama = nama[:20] + "..."

        # Tombol nama / identitas
        customer_button = InlineKeyboardButton(
            f"{nama} | {am} | {idnumber}",
            callback_data=f"customer_{idnumber}"
        )

        # Tombol tunggakan
        tunggakan_button = InlineKeyboardButton(
            "Tunggakan",
            callback_data=f"tunggakan_{idnumber}"
        )

        # Tombol invoice
        invoice_button = InlineKeyboardButton(
            "Invoice",
            callback_data=f"invoice_{idnumber}"
        )

        # SATU CUSTOMER = SATU BARIS
        keyboard.append([
            customer_button,
            tunggakan_button,
            invoice_button
        ])

    # ==========================
    # PAGINATION
    # ==========================

    navigation = []

    if page > 0:

        navigation.append(
            InlineKeyboardButton(
                "Sebelumnya",
                callback_data=f"page_{page - 1}"
            )
        )

    if end < len(customers):

        navigation.append(
            InlineKeyboardButton(
                "Selanjutnya",
                callback_data=f"page_{page + 1}"
            )
        )

    if navigation:
        keyboard.append(navigation)

    return InlineKeyboardMarkup(keyboard)