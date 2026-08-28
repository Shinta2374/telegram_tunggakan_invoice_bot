import os
import pandas as pd


class InvoiceRepository:

    def __init__(self, file_path="data/invoice/invoice.xlsx"):

        self.file_path = file_path
        self._data = None
        self._last_modified = None

    def _normalize_header(self, value):

        return (
            str(value)
            .strip()
            .lower()
            .replace(" ", "")
            .replace(".", "")
            .replace("_", "")
        )

    def _normalize_customer_id(self, value):

        if value is None:
            return ""

        value = str(value).strip()

        if not value:
            return ""

        if value.endswith(".0"):
            value = value[:-2]

        return value

    def _load_file(self):

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(
                f"File invoice tidak ditemukan: {self.file_path}"
            )

        modified_time = os.path.getmtime(
            self.file_path
        )

        if (
            self._data is not None
            and self._last_modified == modified_time
        ):
            return self._data

        dataframe = pd.read_excel(
            self.file_path,
            dtype=str
        )

        dataframe = dataframe.fillna("")

        columns = {}

        for column in dataframe.columns:

            normalized = self._normalize_header(
                column
            )

            columns[normalized] = column

        column_mapping = {
            "contraccountdetail": "customer_id",
            "billpe": "periode",
            "billingamount": "billing_amount",
            "llingamount": "billing_amount",
            "ppn": "ppn",
            "totalamount": "total_amount",
            "stts": "status",
            "status": "status",
            "nojastel": "no_jastel",
        }

        selected_columns = {}

        for normalized, field_name in column_mapping.items():

            if normalized in columns:

                selected_columns[field_name] = (
                    columns[normalized]
                )

        required = [
            "customer_id",
            "periode",
            "billing_amount",
            "ppn",
            "total_amount",
            "status",
        ]

        missing = [
            field
            for field in required
            if field not in selected_columns
        ]

        if missing:

            raise ValueError(
                "Kolom invoice tidak lengkap. "
                f"Kolom yang tidak ditemukan: {missing}"
            )

        result = []

        for _, row in dataframe.iterrows():

            customer_id = (
                self._normalize_customer_id(
                    row[
                        selected_columns[
                            "customer_id"
                        ]
                    ]
                )
            )

            if not customer_id:
                continue

            result.append({
                "customer_id": customer_id,

                "no_jastel": str(
                    row[
                        selected_columns.get(
                            "no_jastel",
                            ""
                        )
                    ]
                ).strip(),

                "periode": str(
                    row[
                        selected_columns[
                            "periode"
                        ]
                    ]
                ).strip(),

                "billing_amount": str(
                    row[
                        selected_columns[
                            "billing_amount"
                        ]
                    ]
                ).strip(),

                "ppn": str(
                    row[
                        selected_columns[
                            "ppn"
                        ]
                    ]
                ).strip(),

                "total_amount": str(
                    row[
                        selected_columns[
                            "total_amount"
                        ]
                    ]
                ).strip(),

                "status": str(
                    row[
                        selected_columns[
                            "status"
                        ]
                    ]
                ).strip(),
            })

        self._data = result
        self._last_modified = modified_time

        return self._data

    def get_all_invoices(self):

        return self._load_file()

    def find_by_customer_id(
        self,
        customer_id
    ):

        customer_id = (
            self._normalize_customer_id(
                customer_id
            )
        )

        invoices = self._load_file()

        return [
            invoice
            for invoice in invoices
            if invoice["customer_id"]
            == customer_id
        ]