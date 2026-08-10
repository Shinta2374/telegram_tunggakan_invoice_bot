from app.services.customer_service import CustomerService
from app.services.tunggakan_service import TunggakanService
from app.services.invoice_service import InvoiceService


def rupiah(value):
    return f"Rp{value:,.0f}".replace(",", ".")


def tampilkan_tunggakan(data):

    print("\n📄 INFORMASI TUNGGAKAN")
    print("-" * 45)

    print(f"Nama          : {data['nama']}")
    print(f"ID Pelanggan  : {data['idnumber']}")
    print(f"Saldo Akhir   : {rupiah(data['saldo_akhir'])}")

    if len(data["tunggakan"]) == 0:

        print("\n✅ Tidak memiliki tunggakan.")

    else:

        print("\nPeriode yang Masih Memiliki Tunggakan\n")

        for item in data["tunggakan"]:

            print(
                f"{item['periode']} : {rupiah(item['nominal'])}"
            )


def main():

    customer_service = CustomerService()
    tunggakan_service = TunggakanService()
    invoice_service = InvoiceService()

    print("=" * 55)
    print(" TELEGRAM CHATBOT SERVICES")
    print("=" * 55)

    while True:

        # ==========================
        # LOGIN
        # ==========================

        idnumber = input(
            "\nMasukkan ID Pelanggan (exit untuk keluar): "
        ).strip()

        if idnumber.lower() == "exit":
            break

        customer = customer_service.find_by_id(idnumber)

        if customer is None:

            print("\n❌ ID Pelanggan tidak ditemukan.")

            continue

        print("\n====================================")
        print(f"Selamat datang, {customer['NAMA']}")
        print("====================================")

        # ==========================
        # MENU
        # ==========================

        while True:

            print("\n1. Informasi Tunggakan")
            print("2. Status Invoice")
            print("3. Ganti ID Pelanggan")
            print("0. Keluar")

            menu = input("\nPilih Menu : ").strip()

            if menu == "1":

                data = tunggakan_service.get_tunggakan(idnumber)

                tampilkan_tunggakan(data)

            elif menu == "2":

                invoice = invoice_service.get_invoice(idnumber)

                print()
                print(invoice["message"])

            elif menu == "3":

                # kembali meminta ID pelanggan
                break

            elif menu == "0":

                return

            else:

                print("\n❌ Menu tidak tersedia.")


if __name__ == "__main__":
    main()