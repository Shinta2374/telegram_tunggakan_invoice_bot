"""
Keyboard untuk memilih Account Manager.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_am_menu(
    ams,
    page=0,
    per_page=5
):

    start = page * per_page
    end = start + per_page

    page_ams = ams[start:end]

    keyboard = []

    for am in page_ams:

        keyboard.append([
            InlineKeyboardButton(
                f"👤 {am}",
                callback_data=f"am:{am}"
            )
        ])

    navigation = []

    if page > 0:

        navigation.append(
            InlineKeyboardButton(
                "◀ Sebelumnya",
                callback_data=f"am_page:{page - 1}"
            )
        )

    if end < len(ams):

        navigation.append(
            InlineKeyboardButton(
                "Selanjutnya ▶",
                callback_data=f"am_page:{page + 1}"
            )
        )

    if navigation:
        keyboard.append(navigation)

    return InlineKeyboardMarkup(keyboard)