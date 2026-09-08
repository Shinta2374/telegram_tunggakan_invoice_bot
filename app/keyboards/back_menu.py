from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup


def get_back_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "Kembali ke Menu",
                callback_data="back_menu"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)