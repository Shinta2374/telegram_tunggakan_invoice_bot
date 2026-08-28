import asyncio

from telegram import Bot

from app.config.settings import settings


async def test_telegram():

    print("=" * 50)
    print("TEST KONEKSI TELEGRAM")
    print("=" * 50)

    if not settings.BOT_TOKEN:
        print("❌ BOT_TOKEN tidak ditemukan")
        return

    print("BOT_TOKEN ditemukan.")

    bot = Bot(
        token=settings.BOT_TOKEN
    )

    try:

        me = await bot.get_me()

        print("✅ Berhasil terhubung ke Telegram")
        print()
        print("Bot ID :", me.id)
        print("Nama   :", me.first_name)
        print("Username :", me.username)

    except Exception as e:

        print("❌ Gagal terhubung ke Telegram")
        print()
        print("Jenis error :", type(e).__name__)
        print("Detail      :", e)

    finally:

        await bot.shutdown()


if __name__ == "__main__":
    asyncio.run(test_telegram())