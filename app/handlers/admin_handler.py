from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from app.config.settings import settings
from app.services.auth_service import AuthService


auth_service = AuthService()

USERS_PER_PAGE = 5


def format_user_name(user):
    first_name = user.get("first_name") or ""
    last_name = user.get("last_name") or ""

    full_name = f"{first_name} {last_name}".strip()

    return full_name if full_name else "-"


def format_username(user):
    username = user.get("username")

    if username:
        return f"@{username}"

    return "-"


def format_datetime(value):
    if not value:
        return "-"

    return value.strftime("%d %b %Y, %H:%M")


def build_admin_dashboard():
    counts = auth_service.get_user_counts()

    pending_users = auth_service.get_users_by_status(
        AuthService.STATUS_PENDING
    )

    approved_users = auth_service.get_users_by_status(
        AuthService.STATUS_APPROVED
    )

    rejected_users = auth_service.get_users_by_status(
        AuthService.STATUS_REJECTED
    )

    text = "👥 DAFTAR USER\n\n"

    text += (
        f"🟡 USER BARU / PENDING "
        f"({counts['pending']})\n"
    )

    if pending_users:
        for index, user in enumerate(pending_users[:5], start=1):
            text += (
                f"{index}. {format_user_name(user)}\n"
                f"   {format_username(user)}\n"
                f"   ID: {user['telegram_id']}\n"
                f"   🕐 {format_datetime(user['requested_at'])}\n\n"
            )
    else:
        text += "Tidak ada user baru.\n\n"

    text += f"🟢 APPROVED ({counts['approved']})\n"

    for index, user in enumerate(approved_users[:5], start=1):
        text += (
            f"{index}. {format_user_name(user)}\n"
            f"   {format_username(user)}\n"
            f"   ID: {user['telegram_id']}\n\n"
        )

    if not approved_users:
        text += "Belum ada user approved.\n\n"

    text += f"🔴 REJECTED ({counts['rejected']})\n"

    for index, user in enumerate(rejected_users[:5], start=1):
        text += (
            f"{index}. {format_user_name(user)}\n"
            f"   {format_username(user)}\n"
            f"   ID: {user['telegram_id']}\n\n"
        )

    if not rejected_users:
        text += "Belum ada user rejected.\n\n"

    text += f"Total user: {counts['total']}"

    keyboard = [
        [
            InlineKeyboardButton(
                "🟡 PENDING",
                callback_data="admin_users:PENDING:0",
            ),
            InlineKeyboardButton(
                "🟢 APPROVED",
                callback_data="admin_users:APPROVED:0",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔴 REJECTED",
                callback_data="admin_users:REJECTED:0",
            ),
            InlineKeyboardButton(
                "👥 SEMUA",
                callback_data="admin_users:ALL:0",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 REFRESH",
                callback_data="admin_refresh",
            ),
        ],
    ]

    return text, InlineKeyboardMarkup(keyboard)


async def show_admin_dashboard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    if not user:
        return

    if user.id not in settings.ADMIN_IDS:
        if update.message:
            await update.message.reply_text(
                "⛔ Anda tidak memiliki akses Admin."
            )

        return

    try:
        text, reply_markup = build_admin_dashboard()

        if update.message:
            await update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
            )

    except Exception as error:
        print(f"[ADMIN ERROR] dashboard: {error}")

        if update.message:
            await update.message.reply_text(
                "⚠️ Gagal mengambil data user."
            )


def build_user_list(
    status,
    page,
):
    if status == "ALL":
        users = auth_service.get_all_users()
        title = "👥 SEMUA USER"
    else:
        users = auth_service.get_users_by_status(status)

        status_title = {
            "PENDING": "🟡 USER PENDING",
            "APPROVED": "🟢 USER APPROVED",
            "REJECTED": "🔴 USER REJECTED",
            "BLOCKED": "⚫ USER BLOCKED",
        }

        title = status_title.get(
            status,
            "👥 DAFTAR USER",
        )

    total_users = len(users)

    start_index = page * USERS_PER_PAGE
    end_index = start_index + USERS_PER_PAGE

    page_users = users[start_index:end_index]

    total_pages = max(
        1,
        (total_users + USERS_PER_PAGE - 1)
        // USERS_PER_PAGE,
    )

    text = (
        f"{title}\n\n"
        f"Total: {total_users}\n\n"
    )

    if not page_users:
        text += "Tidak ada user."

    keyboard = []

    for user in page_users:
        name = format_user_name(user)

        keyboard.append(
            [
                InlineKeyboardButton(
                    name[:30],
                    callback_data=(
                        f"admin_user:{user['telegram_id']}"
                    ),
                )
            ]
        )

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "◀️",
                callback_data=(
                    f"admin_users:{status}:{page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"{page + 1}/{total_pages}",
            callback_data="admin_noop",
        )
    )

    if page < total_pages - 1:
        navigation.append(
            InlineKeyboardButton(
                "▶️",
                callback_data=(
                    f"admin_users:{status}:{page + 1}"
                ),
            )
        )

    keyboard.append(navigation)

    keyboard.append(
        [
            InlineKeyboardButton(
                "REFRESH",
                callback_data=(
                    f"admin_users:{status}:{page}"
                ),
            ),
            InlineKeyboardButton(
                "KEMBALI",
                callback_data="admin_dashboard",
            ),
        ]
    )

    return text, InlineKeyboardMarkup(keyboard)


async def show_user_list(
    query,
    status,
    page,
):
    try:
        page = max(0, int(page))

        text, reply_markup = build_user_list(
            status=status,
            page=page,
        )

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
        )

    except Exception as error:
        print(f"[ADMIN ERROR] user list: {error}")

        await query.answer(
            "Gagal mengambil daftar user.",
            show_alert=True,
        )


def build_user_detail(user):
    text = "👤 DETAIL USER\n\n"

    text += (
        f"Nama:\n"
        f"{format_user_name(user)}\n\n"
        f"Username:\n"
        f"{format_username(user)}\n\n"
        f"Telegram ID:\n"
        f"{user['telegram_id']}\n\n"
        f"Status:\n"
        f"{user['status']}\n\n"
        f"Mendaftar:\n"
        f"{format_datetime(user['requested_at'])}\n"
    )

    if user["approved_at"]:
        text += (
            f"\nACC pada:\n"
            f"{format_datetime(user['approved_at'])}\n"
            f"ACC oleh:\n"
            f"{user['approved_by']}\n"
        )

    if user["rejected_at"]:
        text += (
            f"\nDitolak pada:\n"
            f"{format_datetime(user['rejected_at'])}\n"
            f"Ditolak oleh:\n"
            f"{user['rejected_by']}\n"
        )

    keyboard = []

    if user["status"] == AuthService.STATUS_PENDING:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "✅ TERIMA",
                    callback_data=(
                        f"admin_approve:{user['telegram_id']}"
                    ),
                ),
                InlineKeyboardButton(
                    "❌ TOLAK",
                    callback_data=(
                        f"admin_reject:{user['telegram_id']}"
                    ),
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "↩️ KEMBALI",
                callback_data="admin_dashboard",
            )
        ]
    )

    return text, InlineKeyboardMarkup(keyboard)


async def show_user_detail(
    query,
    telegram_id,
):
    try:
        telegram_id = int(telegram_id)

        user = auth_service.get_user(telegram_id)

        if not user:
            await query.answer(
                "User tidak ditemukan.",
                show_alert=True,
            )
            return

        text, reply_markup = build_user_detail(user)

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
        )

    except Exception as error:
        print(f"[ADMIN ERROR] user detail: {error}")

        await query.answer(
            "Gagal mengambil detail user.",
            show_alert=True,
        )


async def handle_admin_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
):
    admin_id = query.from_user.id

    if admin_id not in settings.ADMIN_IDS:
        await query.answer(
            "⛔ Anda bukan Admin.",
            show_alert=True,
        )
        return

    data = query.data or ""

    if data == "admin_dashboard":
        try:
            text, reply_markup = build_admin_dashboard()

            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
            )

            await query.answer()

        except Exception as error:
            print(
                f"[ADMIN ERROR] dashboard callback: {error}"
            )

            await query.answer(
                "Gagal mengambil data.",
                show_alert=True,
            )

        return

    if data == "admin_refresh":
        try:
            text, reply_markup = build_admin_dashboard()

            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
            )

            await query.answer("Data diperbarui.")

        except Exception as error:
            print(
                f"[ADMIN ERROR] refresh: {error}"
            )

            await query.answer(
                "Gagal memperbarui data.",
                show_alert=True,
            )

        return

    if data == "admin_noop":
        await query.answer()
        return

    if data.startswith("admin_users:"):
        try:
            _, status, page = data.split(":")

            await show_user_list(
                query=query,
                status=status,
                page=int(page),
            )

            await query.answer()

        except Exception as error:
            print(
                f"[ADMIN ERROR] list callback: {error}"
            )

            await query.answer(
                "Data tidak valid.",
                show_alert=True,
            )

        return

    if data.startswith("admin_user:"):
        try:
            telegram_id = data.split(":", 1)[1]

            await show_user_detail(
                query=query,
                telegram_id=telegram_id,
            )

            await query.answer()

        except Exception as error:
            print(
                f"[ADMIN ERROR] detail callback: {error}"
            )

            await query.answer(
                "Data tidak valid.",
                show_alert=True,
            )

        return

    if data.startswith("admin_approve:"):
        telegram_id = int(
            data.split(":", 1)[1]
        )

        user = auth_service.get_user(telegram_id)

        if not user:
            await query.answer(
                "User tidak ditemukan.",
                show_alert=True,
            )
            return

        if user["status"] != AuthService.STATUS_PENDING:
            await query.answer(
                f"User sudah berstatus {user['status']}.",
                show_alert=True,
            )
            return

        updated_user = auth_service.approve_user(
            telegram_id=telegram_id,
            admin_id=admin_id,
        )

        if updated_user:
            try:
                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=(
                        "✅ AKSES DISETUJUI\n\n"
                        "Akun Anda telah disetujui oleh Admin.\n\n"
                        "Silakan gunakan /start "
                        "untuk masuk ke sistem."
                    ),
                )
            except Exception as error:
                print(
                    f"[ADMIN ERROR] notify approved user: {error}"
                )

            text, reply_markup = build_admin_dashboard()

            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
            )

            await query.answer(
                "User berhasil di-ACC."
            )

        return

    if data.startswith("admin_reject:"):
        telegram_id = int(
            data.split(":", 1)[1]
        )

        user = auth_service.get_user(telegram_id)

        if not user:
            await query.answer(
                "User tidak ditemukan.",
                show_alert=True,
            )
            return

        if user["status"] != AuthService.STATUS_PENDING:
            await query.answer(
                f"User sudah berstatus {user['status']}.",
                show_alert=True,
            )
            return

        updated_user = auth_service.reject_user(
            telegram_id=telegram_id,
            admin_id=admin_id,
        )

        if updated_user:
            try:
                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=(
                        "❌ AKSES DITOLAK\n\n"
                        "Maaf, permintaan akses Anda "
                        "telah ditolak oleh Admin."
                    ),
                )
            except Exception as error:
                print(
                    f"[ADMIN ERROR] notify rejected user: {error}"
                )

            text, reply_markup = build_admin_dashboard()

            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
            )

            await query.answer(
                "User berhasil ditolak."
            )

        return