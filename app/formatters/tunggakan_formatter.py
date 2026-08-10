from app.formatters.currency_formatter import CurrencyFormatter


class TunggakanFormatter:

    @staticmethod
    def format(data):

        if data is None:

            return (
                "❌ Data pelanggan tidak ditemukan."
            )

        message = (

            "📄 <b>Informasi Tunggakan</b>\n\n"

            f"<b>Nama</b>\n"
            f"{data['nama']}\n\n"

            f"<b>ID Pelanggan</b>\n"
            f"{data['idnumber']}\n\n"

            f"<b>Saldo Akhir</b>\n"
            f"{CurrencyFormatter.rupiah(data['saldo_akhir'])}\n\n"

        )

        if len(data["tunggakan"]) == 0:

            message += (
                "✅ Tidak memiliki tunggakan."
            )

            return message

        message += (
            "<b>Periode yang Masih Memiliki Tunggakan</b>\n\n"
        )

        for item in data["tunggakan"]:

            message += (

                f"• {item['periode']} : "
                f"{CurrencyFormatter.rupiah(item['nominal'])}\n"

            )

        return message