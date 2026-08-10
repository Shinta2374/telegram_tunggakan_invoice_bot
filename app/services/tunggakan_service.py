"""
Business Logic Informasi Tunggakan
"""

from app.services.customer_service import CustomerService


class TunggakanService:

    def __init__(self):
        self.customer_service = CustomerService()

        # daftar kolom periode yang ingin dicek
        self.periode_columns = [
            "202601",
            "202602",
            "202603",
            "202604",
            "202605",
            "202606",
            "202607",
            "202608",
            "202609",
            "202610",
            "202611",
            "202612",
        ]

    def _to_number(self, value):
        """
        Mengubah nilai spreadsheet menjadi integer.
        """

        if value is None:
            return 0

        value = str(value).strip()

        if value == "":
            return 0

        value = value.replace(".", "")
        value = value.replace(",", "")

        try:
            return int(float(value))
        except:
            return 0

    def get_tunggakan(self, idnumber):

        customer = self.customer_service.find_by_id(idnumber)

        if customer is None:
            return None

        tunggakan = []

        for periode in self.periode_columns:

            nominal = self._to_number(
                customer.get(periode, 0)
            )

            if nominal > 0:

                tunggakan.append({
                    "periode": periode,
                    "nominal": nominal
                })

        return {
            "nama": customer["NAMA"],
            "idnumber": customer["idnumber"],
            "am": customer["AM"],
            "segmen": customer["segmen"],
            "saldo_akhir": self._to_number(
                customer.get("SALDO AKHIR CYC", 0)
            ),
            "tunggakan": tunggakan
        }