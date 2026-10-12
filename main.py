"""Command-line interface for the mini bank."""
import bank


def naira(kobo):
    return f"₦{kobo / 100:,.2f}"


def ask_int(prompt):
    try:
        return int(input(prompt).strip())
    except ValueError:
        raise bank.BankError("Please enter a valid number.")


def run():
    conn = bank.connect()
    actions = {
        "1": "Create account",
        "2": "Deposit",
        "3": "Withdraw",
        "4": "Transfer",
        "5": "Check balance",
        "6": "Transaction history",
        "0": "Exit",
    }
    while True:
        print("\n=== MINI BANK ===")
        for key, label in actions.items():
            print(f"{key}. {label}")
        choice = input("Choose: ").strip()
        try:
            if choice == "1":
                name = input("Full name: ")
                pin = input("Choose a 4-digit PIN: ")
                print(f"Account created. Your account number is {bank.create_account(conn, name, pin)}")
            elif choice == "2":
                acc = ask_int("Account number: ")
                bank.deposit(conn, acc, bank.to_kobo(input("Amount (₦): ")))
                print("Deposit successful.")
            elif choice == "3":
                acc = ask_int("Account number: ")
                pin = input("PIN: ")
                bank.withdraw(conn, acc, pin, bank.to_kobo(input("Amount (₦): ")))
                print("Withdrawal successful.")
            elif choice == "4":
                src = ask_int("Your account number: ")
                pin = input("PIN: ")
                dest = ask_int("Recipient account number: ")
                bank.transfer(conn, src, pin, dest, bank.to_kobo(input("Amount (₦): ")))
                print("Transfer successful.")
            elif choice == "5":
                acc = ask_int("Account number: ")
                print("Balance:", naira(bank.get_balance(conn, acc, input("PIN: "))))
            elif choice == "6":
                acc = ask_int("Account number: ")
                rows = bank.history(conn, acc, input("PIN: "))
                if not rows:
                    print("No transactions yet.")
                for r in rows:
                    extra = f" (account {r['related_account_id']})" if r["related_account_id"] else ""
                    print(f"{r['created_at']}  {r['kind']:<13} {naira(r['amount'])}{extra}")
            elif choice == "0":
                break
            else:
                print("Invalid choice.")
        except bank.BankError as err:
            print(f"Error: {err}")


if __name__ == "__main__":
    run()
