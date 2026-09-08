import re
import unicodedata

from app.services.customer_service import CustomerService


class SearchService:

    def __init__(self):
        self.customer_service = CustomerService()

    def normalize_text(self, value):

        if value is None:
            return ""

        text = str(value).strip().lower()

        text = unicodedata.normalize(
            "NFKD",
            text,
        )

        text = "".join(
            char
            for char in text
            if not unicodedata.combining(char)
        )

        text = text.replace(
            "&",
            " dan ",
        )

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def normalize_customer_id(self, value):

        if value is None:
            return ""

        text = str(value).strip()

        if not text:
            return ""

        try:

            number = float(text)

            if number.is_integer():
                return str(int(number))

        except (
            ValueError,
            TypeError,
        ):
            pass

        return text

    def get_customer_name(self, customer):

        fields = (
            "PELANGGAN",
            "nama",
            "CUSTOMER",
            "pcTCYC",
        )

        for field in fields:

            value = customer.get(field)

            if (
                value is not None
                and str(value).strip()
            ):
                return str(value).strip()

        return "-"

    def get_customer_id(self, customer):

        fields = (
            "idnumber",
            "ID",
            "id",
        )

        for field in fields:

            value = customer.get(field)

            customer_id = (
                self.normalize_customer_id(
                    value
                )
            )

            if customer_id:
                return customer_id

        return ""

    def get_customer_am(self, customer):

        fields = (
            "AM",
            "am",
        )

        for field in fields:

            value = customer.get(field)

            if (
                value is not None
                and str(value).strip()
            ):
                return str(value).strip()

        return ""

    def tokenize(self, value):

        text = self.normalize_text(
            value
        )

        if not text:
            return []

        return text.split()

    def match_customer(
        self,
        keyword,
        customer,
    ):
        query = self.normalize_text(
            keyword
        )

        if not query:
            return 0

        customer_name = (
            self.normalize_text(
                self.get_customer_name(
                    customer
                )
            )
        )

        customer_id = (
            self.normalize_customer_id(
                self.get_customer_id(
                    customer
                )
            )
        )

        query_id = (
            self.normalize_customer_id(
                keyword
            )
        )

        # ==========================================
        # EXACT ID
        # ==========================================

        if (
            query_id
            and customer_id
            and query_id == customer_id
        ):
            return 100

        if not customer_name:
            return 0

        query_tokens = self.tokenize(
            query
        )

        name_tokens = self.tokenize(
            customer_name
        )

        if not query_tokens:
            return 0

        # ==========================================
        # EXACT FULL NAME
        # ==========================================

        if query == customer_name:
            return 100

        # ==========================================
        # EXACT PHRASE
        # ==========================================

        if query in customer_name:
            return 95

        # ==========================================
        # SEMUA TOKEN HARUS COCOK
        # ==========================================

        for query_token in query_tokens:

            token_found = False

            for name_token in name_tokens:

                if (
                    query_token
                    == name_token
                ):
                    token_found = True
                    break

                if (
                    query_token
                    in name_token
                ):
                    token_found = True
                    break

            if not token_found:
                return 0

        # Semua token ditemukan.
        # Semakin banyak token yang cocok,
        # semakin tinggi hasilnya.
        return 90

    def search_customers(
        self,
        keyword,
        customers=None,
        min_score=1,
        max_results=10,
    ):

        keyword = str(
            keyword or ""
        ).strip()

        if not keyword:
            return []

        if customers is None:

            customers = (
                self.customer_service
                .get_all_customers()
            )

        results = []

        for customer in customers:

            score = self.match_customer(
                keyword,
                customer,
            )

            if score < min_score:
                continue

            results.append(
                {
                    "customer": customer,
                    "score": score,
                    "customer_id": (
                        self.get_customer_id(
                            customer
                        )
                    ),
                    "customer_name": (
                        self.get_customer_name(
                            customer
                        )
                    ),
                    "am": (
                        self.get_customer_am(
                            customer
                        )
                    ),
                }
            )

        results.sort(
            key=lambda item: (
                item["score"],
                item["customer_name"].lower(),
            ),
            reverse=True,
        )

        return results[
            :max_results
        ]

    def search_customer(
        self,
        keyword,
        customers=None,
    ):

        results = self.search_customers(
            keyword=keyword,
            customers=customers,
            min_score=1,
            max_results=10,
        )

        if len(results) == 1:
            return results[0]

        return None

    def search_ams(
        self,
        keyword,
        customers=None,
        max_results=10,
    ):

        keyword = str(
            keyword or ""
        ).strip()

        if not keyword:
            return []

        if customers is None:

            customers = (
                self.customer_service
                .get_all_customers()
            )

        am_names = set()

        for customer in customers:

            am = self.get_customer_am(
                customer
            )

            if am:
                am_names.add(am)

        query = self.normalize_text(
            keyword
        )

        query_tokens = self.tokenize(
            query
        )

        results = []

        for am in am_names:

            normalized_am = (
                self.normalize_text(
                    am
                )
            )

            am_tokens = self.tokenize(
                normalized_am
            )

            if query == normalized_am:

                score = 100

            elif query in normalized_am:

                score = 95

            else:

                matched = True

                for query_token in query_tokens:

                    token_found = False

                    for am_token in am_tokens:

                        if (
                            query_token
                            == am_token
                        ):
                            token_found = True
                            break

                        if (
                            query_token
                            in am_token
                        ):
                            token_found = True
                            break

                    if not token_found:
                        matched = False
                        break

                if not matched:
                    continue

                score = 90

            results.append(
                {
                    "am": am,
                    "score": score,
                }
            )

        results.sort(
            key=lambda item: (
                item["score"],
                item["am"].lower(),
            ),
            reverse=True,
        )

        return results[
            :max_results
        ]

    def is_customer_id(
        self,
        keyword,
    ):

        keyword = str(
            keyword or ""
        ).strip()

        if not keyword:
            return False

        normalized = (
            self.normalize_customer_id(
                keyword
            )
        )

        return normalized.isdigit()