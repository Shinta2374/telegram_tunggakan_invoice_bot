"""
Testing Tunggakan Service
"""

from app.services.tunggakan_service import TunggakanService


def format_rupiah(value):

    return "Rp" + f"{value:,.0f}".replace(",", ".")


def main():

    print("=" * 60)
    print("TEST TUNGGAKAN SERVICE")
    print("=" * 60)

    service = TunggakanService()

    while True:

        print()

        idnumber = input(
            "Masukkan ID Pelanggan "
            "(exit untuk keluar): "
        ).strip()

        if idnumber.lower() == "exit":

            print()
            print("Program selesai.")

            break

        if not idnumber:

            print(
                "❌ ID Pelanggan tidak boleh kosong."
            )

            continue

        result = service.get_tunggakan(
            idnumber
        )

        if result is None:

            print()
            print(
                "❌ ID Pelanggan tidak ditemukan."
            )

            continue

        # =====================================
        # INFORMASI CUSTOMER
        # =====================================

        print()
        print("===== INFORMASI CUSTOMER =====")

        print(
            "Nama          :",
            result.get("nama") or "-"
        )

        print(
            "AM            :",
            result.get("am") or "-"
        )

        print(
            "ID Pelanggan  :",
            result.get("idnumber") or "-"
        )

        print(
            "Saldo Akhir   :",
            format_rupiah(
                result.get(
                    "saldo_akhir",
                    0
                )
            )
        )

        # =====================================
        # AGING
        # =====================================

        print()
        print("===== AGING TUNGGAKAN =====")

        aging = result.get(
            "aging",
            []
        )

        if aging:

            for item in aging:

                print(
                    f"{item['periode']:<15}: "
                    f"{format_rupiah(item['nominal'])}"
                )

        else:

            print(
                "Tidak ada aging "
                "7 bulan ke atas."
            )

        # =====================================
        # TUNGGAKAN PERIODE
        # =====================================

        print()
        print("===== TUNGGAKAN PERIODE =====")

        tunggakan = result.get(
            "tunggakan_periode",
            []
        )

        if tunggakan:

            for item in tunggakan:

                print(
                    f"{item['periode']:<15}: "
                    f"{format_rupiah(item['nominal'])}"
                )

        else:

            print(
                "Tidak ada tunggakan periode."
            )

        print()
        print("=" * 60)


if __name__ == "__main__":
    main()