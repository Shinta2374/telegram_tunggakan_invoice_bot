"""
Business Logic Customer
"""

from app.repositories.spreadsheet_repository import SpreadsheetRepository


class CustomerService:

    def __init__(self):
        self.repository = SpreadsheetRepository()

    def get_all_customers(self):
        """
        Mengambil seluruh customer dari Spreadsheet.

        Data Spreadsheet hanya dibaca.
        Tidak ada proses write/update ke Spreadsheet.
        """

        df = self.repository.get_dataframe()

        return df.to_dict("records")

    def find_by_id(self, idnumber):
        """
        Mencari customer berdasarkan ID pelanggan.
        """

        customers = self.get_all_customers()

        target_id = str(idnumber).strip()

        for customer in customers:

            customer_id = str(
                customer.get("idnumber", "")
            ).strip()

            if customer_id == target_id:
                return customer

        return None

    def get_all_ams(self):
        """
        Mengambil daftar AM unik.

        Sorting hanya dilakukan di memory.
        Tidak mengubah Spreadsheet.
        """

        customers = self.get_all_customers()

        ams = set()

        for customer in customers:

            am = str(
                customer.get("AM", "")
            ).strip()

            if am:
                ams.add(am)

        return sorted(ams, key=str.lower)

    def get_customers_by_am(self, am):
        """
        Mengambil customer berdasarkan AM.
        """

        customers = self.get_all_customers()

        target_am = str(am).strip().lower()

        result = []

        for customer in customers:

            customer_am = str(
                customer.get("AM", "")
            ).strip().lower()

            if customer_am == target_am:
                result.append(customer)

        # Sorting hanya pada data di memory
        result.sort(
            key=lambda x: str(
                x.get("NAMA", "")
            ).strip().lower()
        )

        return result