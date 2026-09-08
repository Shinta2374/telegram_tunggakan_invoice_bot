from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_customer_keyboard(
    customer,
    index: int
):

    customer_id = str(customer.get("idnumber", "")).strip()

    keyboard = [
        [
            InlineKeyboardButton(
                "Tunggakan",
                callback_data=f"tunggakan:{customer_id}"
            ),
            InlineKeyboardButton(
                "Invoice",
                callback_data=f"invoice:{customer_id}"
            )
        ]
    ]

    return keyboard


def get_pagination_keyboard(
    current_page: int,
    total_pages: int
):

    keyboard = []

    navigation = []

    if current_page > 0:
        navigation.append(
            InlineKeyboardButton(
                "Sebelumnya",
                callback_data=f"customer_page:{current_page - 1}"
            )
        )

    if current_page < total_pages - 1:
        navigation.append(
            InlineKeyboardButton(
                "Selanjutnya",
                callback_data=f"customer_page:{current_page + 1}"
            )
        )

    if navigation:
        keyboard.append(navigation)

    keyboard.append(
        [
            InlineKeyboardButton(
                "Cari Customer",
                callback_data="search_customer"
            )
        ]
    )

    return keyboard