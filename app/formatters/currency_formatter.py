class CurrencyFormatter:

    @staticmethod
    def rupiah(value):

        if value is None:
            value = 0

        return (
            f"Rp{value:,.0f}"
            .replace(",", ".")
        )