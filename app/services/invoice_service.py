from pathlib import Path

from openpyxl import load_workbook


class InvoiceService:

    def __init__(self):

        self.file_path = Path(
            "data"
        ) / "invoice" / "invoice.xlsx"

    # CEK FILE

    def file_exists(self):

        return self.file_path.exists()

    # NORMALISASI TEXT

    def _normalize_text(self, value):

        if value is None:
            return ""

        return (
            str(value)
            .replace("\xa0", " ")
            .strip()
        )

    # NORMALISASI CUSTOMER ID

    def _normalize_customer_id(self, value):

        if value is None:
            return ""

        text = (
            str(value)
            .replace("\xa0", "")
            .strip()
        )

        if not text:
            return ""

        # Contoh:
        # 4806453.0 -> 4806453
        if text.endswith(".0"):

            try:

                number = float(text)

                if number.is_integer():

                    return str(
                        int(number)
                    )

            except (
                ValueError,
                TypeError,
            ):
                pass

        # Jika Excel membaca sebagai float
        try:

            number = float(text)

            if number.is_integer():

                return str(
                    int(number)
                )

        except (
            ValueError,
            TypeError,
        ):
            pass

        return text
    
    # KONVERSI ANGKA

    def _to_number(self, value):

        if value is None:
            return 0

        if isinstance(value, bool):
            return 0

        if isinstance(value, (int, float)):

            try:

                if value != value:
                    return 0

                return float(value)

            except Exception:
                return 0

        text = self._normalize_text(
            value
        )

        if not text:
            return 0

        # Hilangkan Rp dan spasi
        text = (
            text
            .replace("Rp", "")
            .replace("rp", "")
            .replace(" ", "")
        )

        # Format Indonesia:
        #
        # 101.536.997
        # 11.169.070
        #
        # menjadi:
        #
        # 101536997
        if "." in text and "," not in text:

            parts = text.split(".")

            if all(
                part.isdigit()
                for part in parts
            ):

                # Jika titik digunakan sebagai
                # pemisah ribuan
                if all(
                    len(part) == 3
                    for part in parts[1:]
                ):

                    text = "".join(parts)

        # Format:
        #
        # 101.536.997,50
        #
        # menjadi:
        #
        # 101536997.50
        elif "." in text and "," in text:

            text = (
                text
                .replace(".", "")
                .replace(",", ".")
            )

        # Format:
        #
        # 101536997,50
        #
        elif "," in text:

            text = text.replace(
                ",",
                "."
            )

        try:

            return float(text)

        except (
            ValueError,
            TypeError,
        ):

            return 0

    # NORMALISASI STATUS

    def _normalize_status(self, value):

        status = (
            self._normalize_text(value)
            .lower()
        )

        if not status:

            return "Belum Terkirim"

        # BELUM TERKIRIM

        if (
            "no data to display"
            in status
        ):

            return "Belum Terkirim"

        # ON PROGRESS
 
        if status in (
            "#n/a",
            "n/a",
        ):

            return "On Progress"

        if "#n/a" in status:

            return "On Progress"

        # INVOICE MANUAL

        manual_keywords = [
            "inv manual",
            "invoice manual",
            "sent tghn manual",
            "sent manual",
            "manual via ideas",
            "klik sent manual",
        ]

        for keyword in manual_keywords:

            if keyword in status:

                return "Invoice Manual"

        # FALLBACK
        # Kalau ada status baru di Excel yang
        # belum kita mapping, tampilkan nilai
        # aslinya agar tidak kehilangan informasi.
        #

        return self._normalize_text(
            value
        )

        # MEMBACA WORKBOOK
   
    def _load_workbook(self):

        if not self.file_exists():

            raise FileNotFoundError(
                "File invoice tidak ditemukan: "
                f"{self.file_path}"
            )

        try:

            return load_workbook(
                filename=self.file_path,
                data_only=True,
                read_only=True,
            )

        except Exception as e:

            raise ValueError(
                "File invoice tidak dapat dibaca: "
                f"{e}"
            )

    # MENCARI HEADER

    def _find_header_row(self, worksheet):

        required_headers = {
            "no.jastel": None,
            "contr.account detail": None,
            "bill.pe": None,
            "ppn": None,
            "total amount": None,
            "stts": None,
        }

        # periksa maksimal 20 baris pertama, header berada pada baris pertama.
        
        max_check = min(
            worksheet.max_row,
            20
        )

        for row_number in range(
            1,
            max_check + 1
        ):

            found = {}

            for cell in worksheet[row_number]:

                value = self._normalize_text(
                    cell.value
                )

                normalized = (
                    value
                    .lower()
                    .replace(" ", "")
                )

                if normalized == "nojastel":
                    found["no.jastel"] = cell.column

                elif normalized == "contr.accountdetail":
                    found[
                        "contr.account detail"
                    ] = cell.column

                elif normalized == "bill.pe":
                    found["bill.pe"] = cell.column

                elif normalized == "ppn":
                    found["ppn"] = cell.column

                elif normalized == "totalamount":
                    found[
                        "total amount"
                    ] = cell.column

                elif normalized == "stts":
                    found["stts"] = cell.column

            # Billing Amount terbaca sebagai "lling Amount", sehingga

            if (
                "no.jastel" in found
                and "contr.account detail" in found
                and "bill.pe" in found
                and "ppn" in found
                and "total amount" in found
                and "stts" in found
            ):
                
                #billing ammount sebelum ppn
                if "ppn" in found:

                    ppn_column = found["ppn"]

                    found[
                        "billing amount"
                    ] = ppn_column - 1

                return (
                    row_number,
                    found
                )

        return None

       # FALLBACK STRUKTUR YANG SUDAH DIVERIFIKASI

    def _get_verified_columns(self):

        return {
            "no": 1,
            "no.jastel": 2,
            "contr.account detail": 3,
            "bill.pe": 4,
            "billing amount": 5,
            "ppn": 6,
            "total amount": 7,
            "stts": 8,
        }

        # AMBIL DATA INVOICE CUSTOMER

    def get_customer_invoice_data(
        self,
        customer_id,
    ):

        target_id = (
            self._normalize_customer_id(
                customer_id
            )
        )

        print(
            "[INVOICE SEARCH] "
            f"Target RAW='{customer_id}' "
            f"Target NORMALIZED='{target_id}'"
        )

        if not target_id:

            return []

        workbook = self._load_workbook()

        invoices = []

        try:

            for worksheet in workbook.worksheets:

                print(
                    "======================================"
                )

                print(
                    f"[INVOICE SHEET] "
                    f"{worksheet.title}"
                )

                header_result = (
                    self._find_header_row(
                        worksheet
                    )
                )

                # HEADER DITEMUKAN

                if header_result:

                    (
                        header_row,
                        columns
                    ) = header_result

                    print(
                        "[INVOICE HEADER] "
                        f"Row={header_row}"
                    )

                    no_jastel_col = columns[
                        "no.jastel"
                    ]

                    customer_name_col = columns[
                        "contr.account detail"
                    ]

                    periode_col = columns[
                        "bill.pe"
                    ]

                    billing_col = columns[
                        "billing amount"
                    ]

                    ppn_col = columns[
                        "ppn"
                    ]

                    total_col = columns[
                        "total amount"
                    ]

                    status_col = columns[
                        "stts"
                    ]

                    start_row = (
                        header_row + 1
                    )

                # --------------------------------------------------
                # FALLBACK
                # --------------------------------------------------
                #
                # Struktur file sudah diverifikasi:
                #
                # A No
                # B No.Jastel
                # C Contr.Account Detail
                # D Bill.Pe
                # E lling Amount
                # F PPN
                # G Total Amount
                # H Stts
                #
                # Jadi kalau header gagal dikenali karena
                # perubahan whitespace/format Excel,
                # kita tetap bisa membaca struktur yang
                # sudah diketahui.
                #

                else:

                    print(
                        "[INVOICE HEADER] "
                        "Header tidak dikenali. "
                        "Menggunakan struktur kolom "
                        "invoice terverifikasi."
                    )

                    columns = (
                        self._get_verified_columns()
                    )

                    no_jastel_col = columns[
                        "no.jastel"
                    ]

                    customer_name_col = columns[
                        "contr.account detail"
                    ]

                    periode_col = columns[
                        "bill.pe"
                    ]

                    billing_col = columns[
                        "billing amount"
                    ]

                    ppn_col = columns[
                        "ppn"
                    ]

                    total_col = columns[
                        "total amount"
                    ]

                    status_col = columns[
                        "stts"
                    ]

                    start_row = 1

                # --------------------------------------------------
                # BACA BARIS
                # --------------------------------------------------

                for row_number in range(
                    start_row,
                    worksheet.max_row + 1
                ):

                    raw_customer_id = (
                        worksheet.cell(
                            row=row_number,
                            column=no_jastel_col,
                        ).value
                    )

                    normalized_id = (
                        self._normalize_customer_id(
                            raw_customer_id
                        )
                    )

                    if normalized_id != target_id:

                        continue

                    raw_customer_name = (
                        worksheet.cell(
                            row=row_number,
                            column=customer_name_col,
                        ).value
                    )

                    raw_periode = (
                        worksheet.cell(
                            row=row_number,
                            column=periode_col,
                        ).value
                    )

                    raw_billing = (
                        worksheet.cell(
                            row=row_number,
                            column=billing_col,
                        ).value
                    )

                    raw_ppn = (
                        worksheet.cell(
                            row=row_number,
                            column=ppn_col,
                        ).value
                    )

                    raw_total = (
                        worksheet.cell(
                            row=row_number,
                            column=total_col,
                        ).value
                    )

                    raw_status = (
                        worksheet.cell(
                            row=row_number,
                            column=status_col,
                        ).value
                    )

                    invoice = {
                        "customer_id": target_id,

                        "pelanggan": (
                            self._normalize_text(
                                raw_customer_name
                            )
                        ),

                        "periode": (
                            self._normalize_text(
                                raw_periode
                            )
                        ),

                        "billing_amount": (
                            self._to_number(
                                raw_billing
                            )
                        ),

                        "ppn": (
                            self._to_number(
                                raw_ppn
                            )
                        ),

                        "total_amount": (
                            self._to_number(
                                raw_total
                            )
                        ),

                        "status": (
                            self._normalize_status(
                                raw_status
                            )
                        ),

                        "status_raw": (
                            self._normalize_text(
                                raw_status
                            )
                        ),

                        "sheet": worksheet.title,

                        "row": row_number,
                    }

                    invoices.append(
                        invoice
                    )

                    print(
                        "[INVOICE MATCH] "
                        f"Row={row_number} "
                        f"ID={normalized_id} "
                        f"Periode={invoice['periode']} "
                        f"Status={invoice['status']}"
                    )

        finally:

            workbook.close()

        print(
            "======================================"
        )

        print(
            "[INVOICE RESULT] "
            f"Target ID = {target_id} "
            f"Jumlah invoice = {len(invoices)}"
        )

        return invoices