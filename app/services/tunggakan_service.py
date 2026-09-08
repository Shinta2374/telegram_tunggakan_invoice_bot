from app.services.customer_service import CustomerService


class TunggakanService:

    def __init__(self):

        self.customer_service = CustomerService()

        self.aging_columns = [
            ("7–12 bulan", "7-12_bln"),
            ("13–24 bulan", "13-24_bln"),
            ("> 24 bulan", ">_24_bln"),
        ]

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

        if value is None:
            return 0

        try:

            if isinstance(value, float):

                if value != value:
                    return 0

                return value

            value = str(value).strip()

            if not value:
                return 0

            value = (
                value
                .replace("Rp", "")
                .replace(" ", "")
            )

            if "." in value and "," not in value:

                parts = value.split(".")

                if all(
                    len(part) == 3
                    for part in parts[1:]
                ):
                    value = "".join(parts)

            elif "." in value and "," in value:

                value = (
                    value
                    .replace(".", "")
                    .replace(",", ".")
                )

            elif "," in value:

                value = value.replace(
                    ",",
                    ".",
                )

            return float(value)

        except (
            ValueError,
            TypeError,
        ):
            return 0

    def _get_period_value(
        self,
        customer,
        periode,
    ):

        value = customer.get(periode)

        if value is not None:
            return value

        value = customer.get(
            f"{periode}.0"
        )

        if value is not None:
            return value

        return 0

    def get_customers_with_tunggakan(
        self,
        am,
    ):

        customers = (
            self.customer_service
            .get_customers_by_am(am)
        )

        result = []

        for customer in customers:

            saldo = self._to_number(
                customer.get(
                    "SALDO AKHIR CYC"
                )
            )

            if saldo > 0:

                customer_copy = (
                    customer.copy()
                )

                customer_copy[
                    "total_tunggakan"
                ] = saldo

                result.append(
                    customer_copy
                )

        result.sort(
            key=lambda x: x.get(
                "total_tunggakan",
                0
            ),
            reverse=True,
        )

        return result

    def get_tunggakan(
        self,
        idnumber,
    ):

        customer = (
            self.customer_service
            .find_by_id(idnumber)
        )

        if customer is None:
            return None

        pelanggan = (
            customer.get("pcTCYC")
            or customer.get("PELANGGAN")
            or customer.get("pelanggan")
            or "-"
        )

        am = (
            customer.get("AM")
            or customer.get("am")
            or "-"
        )

        saldo_akhir_cyc = self._to_number(
            customer.get(
                "SALDO AKHIR CYC"
            )
        )

        aging = []

        for label, column in self.aging_columns:

            nominal = self._to_number(
                customer.get(column)
            )

            if nominal > 0:

                aging.append({
                    "periode": label,
                    "nominal": nominal,
                })

        tunggakan_periode = []

        for periode in self.periode_columns:

            value = self._get_period_value(
                customer,
                periode,
            )

            nominal = self._to_number(
                value
            )

            if nominal > 0:

                tunggakan_periode.append({
                    "periode": periode,
                    "nominal": nominal,
                })

        return {
            "PELANGGAN": pelanggan,
            "am": am,
            "idnumber": (
                customer.get("idnumber")
                or idnumber
            ),
            "saldo_akhir_cyc": (
                saldo_akhir_cyc
            ),
            "aging": aging,
            "tunggakan_periode": (
                tunggakan_periode
            ),
        }