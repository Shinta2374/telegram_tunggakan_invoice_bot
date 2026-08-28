import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    APP_NAME = os.getenv("APP_NAME", "Telegram Chatbot Services")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

    BOT_TOKEN = os.getenv("BOT_TOKEN")

    GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    GOOGLE_SHEET_GID = os.getenv("GOOGLE_SHEET_GID")
    WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")

    @property
    def GOOGLE_SHEET_CSV_URL(self):
        return (
            f"https://docs.google.com/spreadsheets/d/"
            f"{self.GOOGLE_SHEET_ID}"
            f"/export?format=csv&gid={self.GOOGLE_SHEET_GID}"
        )


settings = Settings()