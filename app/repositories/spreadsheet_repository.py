import pandas as pd

from app.config.settings import settings


class SpreadsheetRepository:

    def __init__(self):
        self.csv_url = settings.GOOGLE_SHEET_CSV_URL

    def get_dataframe(self):

        try:
            # Ambil seluruh data
            df = pd.read_csv(
                self.csv_url,
                header=None
            )

            # Header sebenarnya ada di baris kedua
            header_row = 1

            df.columns = df.iloc[header_row]

            # Hapus baris kosong dan header
            df = df.iloc[header_row + 1:].reset_index(drop=True)

            # Rapikan nama kolom
            df.columns = (
                df.columns
                .astype(str)
                .str.strip()
            )

            return df

        except Exception as e:
            raise Exception(
                f"Gagal membaca Spreadsheet.\n{e}"
            )