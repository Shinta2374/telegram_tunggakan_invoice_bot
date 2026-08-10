from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup


def get_main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "📄 Informasi Tunggakan",
                callback_data="tunggakan"
            )
        ],

        [
            InlineKeyboardButton(
                "📧 Status Invoice",
                callback_data="invoice"
            )
        ],

        [
            InlineKeyboardButton(
                "🔄 Ganti ID Pelanggan",
                callback_data="change_id"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)