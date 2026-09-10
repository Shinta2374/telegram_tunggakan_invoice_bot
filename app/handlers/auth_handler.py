from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from app.config.settings import settings
from app.services.auth_service import AuthService
from app.handlers.start_handler import start


auth_service = AuthService()


PENDING_MESSAGE = (
    "⏳ MENUNGGU PERSETUJUAN ADMIN\n\n"
    "Akun Anda berhasil didaftarkan ke sistem dan sedang "
    "menunggu persetujuan (ACC) dari Admin.\n\n"
    "Anda akan menerima notifikasi jika akses sudah diberikan."
)


REJECTED_MESSAGE = (
    "❌ AKSES DITOLAK\n\n"
    "Maaf, permintaan akses Anda belum disetujui oleh Admin."
)


BLOCKED_MESSAGE = (
    "🚫 AKSES DIBLOKIR\n\n"
    "Akun Anda tidak memiliki akses ke sistem."
)


ERROR_MESSAGE = (
    "⚠️ Terjadi kesalahan saat memproses akun Anda.\n"
    "Silakan coba beberapa saat lagi."
)


async def auth_start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    if not user or not update.message:
        return

    telegram_id = user.id

    if telegram_id in settings.ADMIN_IDS:
        await start(update, context)
        return

    try:
        existing_user = auth_service.get_user(
            telegram_id
        )

        if existing_user:
            status = existing_user["status"]

            if status == AuthService.STATUS_APPROVED:
                await start(update, context)
                return

            if status == AuthService.STATUS_PENDING:
                await update.message.reply_text(
                    PENDING_MESSAGE
                )
                return

            if status == AuthService.STATUS_REJECTED:
                await update.message.reply_text(
                    REJECTED_MESSAGE
                )
                return

            if status == AuthService.STATUS_BLOCKED:
                await update.message.reply_text(
                    BLOCKED_MESSAGE
                )
                return

        registered_user = auth_service.register_user(
            telegram_id=telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )

        if not registered_user:
            await update.message.reply_text(
                ERROR_MESSAGE
            )
            return

        await update.message.reply_text(
            PENDING_MESSAGE
        )

        await notify_admins(
            context.bot,
            registered_user,
        )

    except Exception as error:
        print(
            f"[AUTH ERROR] start: {error}"
        )

        await update.message.reply_text(
            ERROR_MESSAGE
        )


async def notify_admins(
    bot,
    user,
):
    telegram_id = user["telegram_id"]

    username = user.get("username")

    if username:
        username_text = f"@{username}"
    else:
        username_text = "-"

    first_name = user.get("first_name") or "-"
    last_name = user.get("last_name") or "-"

    full_name = f"{first_name} {last_name}".strip()

    message = (
        "🔔 PERMINTAAN AKSES BARU\n\n"
        f"👤 Nama: {full_name}\n"
        f"📱 Username: {username_text}\n"
        f"🆔 Telegram ID: {telegram_id}\n\n"
        "📌 Status: PENDING\n\n"
        "Silakan pilih tindakan:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ TERIMA",
                callback_data=f"auth_approve:{telegram_id}",
            ),
            InlineKeyboardButton(
                "❌ TOLAK",
                callback_data=f"auth_reject:{telegram_id}",
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=message,
                reply_markup=reply_markup,
            )

            print(
                f"[AUTH] Notification sent to admin {admin_id} "
                f"for user {telegram_id}"
            )

        except Exception as error:
            print(
                f"[AUTH ERROR] Failed to notify admin "
                f"{admin_id}: {error}"
            )


async def handle_auth_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
):
    data = query.data

    if data.startswith("auth_approve:"):
        action = "approve"

    elif data.startswith("auth_reject:"):
        action = "reject"

    else:
        return

    try:
        telegram_id = int(
            data.split(":", 1)[1]
        )

    except (ValueError, IndexError):
        await query.answer(
            "Data tidak valid.",
            show_alert=True,
        )
        return

    admin_id = query.from_user.id

    if admin_id not in settings.ADMIN_IDS:
        await query.answer(
            "⛔ Anda bukan Admin.",
            show_alert=True,
        )
        return

    target_user = auth_service.get_user(
        telegram_id
    )

    if not target_user:
        await query.answer(
            "User tidak ditemukan.",
            show_alert=True,
        )
        return

    current_status = target_user["status"]

    if current_status != AuthService.STATUS_PENDING:
        await query.answer(
            f"User sudah berstatus {current_status}.",
            show_alert=True,
        )
        return

    if action == "approve":
        updated_user = auth_service.approve_user(
            telegram_id=telegram_id,
            admin_id=admin_id,
        )

        result_text = "APPROVED"
        admin_status = "✅ AKSES DISETUJUI"

    else:
        updated_user = auth_service.reject_user(
            telegram_id=telegram_id,
            admin_id=admin_id,
        )

        result_text = "REJECTED"
        admin_status = "❌ AKSES DITOLAK"

    if not updated_user:
        await query.answer(
            "Gagal memperbarui status user.",
            show_alert=True,
        )
        return

    await query.answer(
        result_text
    )

    admin_message = (
        f"{admin_status}\n\n"
        f"👤 Nama: "
        f"{updated_user.get('first_name') or '-'} "
        f"{updated_user.get('last_name') or ''}\n"
        f"🆔 Telegram ID: {telegram_id}\n\n"
        f"Status: {result_text}"
    )

    try:
        await query.edit_message_text(
            text=admin_message
        )
    except Exception as error:
        print(
            f"[AUTH ERROR] Failed to edit admin message: {error}"
        )

    if action == "approve":
        user_message = (
            "✅ AKSES DISETUJUI\n\n"
            "Akun Anda telah disetujui oleh Admin.\n\n"
            "Silakan gunakan /start untuk masuk ke sistem."
        )
    else:
        user_message = (
            "❌ AKSES DITOLAK\n\n"
            "Maaf, permintaan akses Anda telah "
            "ditolak oleh Admin."
        )

    try:
        await context.bot.send_message(
            chat_id=telegram_id,
            text=user_message,
        )

    except Exception as error:
        print(
            f"[AUTH ERROR] Failed to notify user "
            f"{telegram_id}: {error}"
        )