from app.services.customer_service import CustomerService


class TunggakanService:
    def __init__(self):
        self.customer_service = CustomerService()

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

        self.aging_columns = [
            ("0-3 bulan", "0-3_bln"),
            ("4-6 bulan", "4-6_bln"),
            ("7-12 bulan", "7-12_bln"),
            ("13-24 bulan", "13-24_bln"),
            ("> 24 bulan", ">_24_bln"),
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
                .replace("rp", "")
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
        value = customer.get(
            periode
        )

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
            saldo_cyc = self._to_number(
                customer.get(
                    "SALDO AKHIR CYC"
                )
            )

            if saldo_cyc != 0:
                customer_copy = (
                    customer.copy()
                )

                customer_copy[
                    "total_tunggakan"
                ] = saldo_cyc

                result.append(
                    customer_copy
                )

        result.sort(
            key=lambda x: x.get(
                "total_tunggakan",
                0,
            ),
            reverse=True,
        )

        return result

    def get_customers_with_saldo_cr(
        self,
        am,
    ):
        customers = (
            self.customer_service
            .get_customers_by_am(am)
        )

        result = []

        for customer in customers:
            saldo_cr = self._to_number(
                customer.get(
                    "saldo_akhir"
                )
            )

            if saldo_cr != 0:
                customer_copy = (
                    customer.copy()
                )

                customer_copy[
                    "total_saldo_cr"
                ] = saldo_cr

                result.append(
                    customer_copy
                )

        result.sort(
            key=lambda x: x.get(
                "total_saldo_cr",
                0,
            ),
            reverse=True,
        )

        return result

    def get_saldo_cyc(
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

        saldo_akhir_cyc = (
            self._to_number(
                customer.get(
                    "SALDO AKHIR CYC"
                )
            )
        )

        # SALDO CR HARUS MENGAMBIL
        # LANGSUNG DARI KOLOM saldo_akhir
        saldo_akhir = (
            self._to_number(
                customer.get(
                    "saldo_akhir"
                )
            )
        )

        saldo_cyc_periode = []

        for periode in self.periode_columns:
            value = self._get_period_value(
                customer,
                periode,
            )

            nominal = self._to_number(
                value
            )

            saldo_cyc_periode.append(
                {
                    "periode": periode,
                    "nominal": nominal,
                }
            )

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
            "saldo_akhir": saldo_akhir,
            "saldo_cyc_periode": (
                saldo_cyc_periode
            ),
        }

    def get_saldo_cr(
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

        # SALDO CR
        # LANGSUNG DARI KOLOM saldo_akhir
        saldo_akhir = (
            self._to_number(
                customer.get(
                    "saldo_akhir"
                )
            )
        )

        # SALDO CYC
        saldo_akhir_cyc = (
            self._to_number(
                customer.get(
                    "SALDO AKHIR CYC"
                )
            )
        )

        aging = []

        for label, column in self.aging_columns:
            nominal = self._to_number(
                customer.get(column)
            )

            aging.append(
                {
                    "periode": label,
                    "nominal": nominal,
                }
            )

        return {
            "PELANGGAN": pelanggan,
            "am": am,
            "idnumber": (
                customer.get("idnumber")
                or idnumber
            ),
            "saldo_akhir": saldo_akhir,
            "saldo_akhir_cyc": (
                saldo_akhir_cyc
            ),
            "aging": aging,
        }

    def get_tunggakan(
        self,
        idnumber,
    ):
        return self.get_saldo_cyc(
            idnumber
        )