from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_am_menu(
    ams,
    page=0,
    per_page=6,
):
    if not ams:
        return InlineKeyboardMarkup([])

    total_pages = (
        len(ams) + per_page - 1
    ) // per_page

    page = max(
        0,
        min(page, total_pages - 1),
    )

    start = page * per_page
    end = min(
        start + per_page,
        len(ams),
    )

    page_ams = ams[start:end]

    keyboard = []

    row = []

    for am in page_ams:
        display_name = str(am).strip()

        if display_name.upper().startswith("AM "):
            display_name = display_name[3:].strip()

        row.append(
            InlineKeyboardButton(
                display_name,
                callback_data=f"select_am:{am}",
            )
        )

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "Sebelumnya",
                callback_data=f"am_page:{page - 1}",
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"{page + 1}/{total_pages}",
            callback_data="noop",
        )
    )

    if page < total_pages - 1:
        navigation.append(
            InlineKeyboardButton(
                "selanjutnya",
                callback_data=f"am_page:{page + 1}",
            )
        )

    keyboard.append(navigation)

    return InlineKeyboardMarkup(keyboard)