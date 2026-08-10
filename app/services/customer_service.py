# Business Logic Customer

from app.repositories.spreadsheet_repository import SpreadsheetRepository


class CustomerService:

    def __init__(self):
        self.repository = SpreadsheetRepository()
        self.df = self.repository.get_dataframe()

    def find_by_id(self, idnumber: str):
        """
        Mencari pelanggan berdasarkan ID.
        """

        # Pastikan kolom idnumber berupa string
        self.df["idnumber"] = (
            self.df["idnumber"]
            .astype(str)
            .str.strip()
        )

        idnumber = str(idnumber).strip()

        customer = self.df[
            self.df["idnumber"] == idnumber
        ]

        if customer.empty:
            return None

        return customer.iloc[0].to_dict()