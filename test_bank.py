import pytest

import bank


@pytest.fixture
def conn():
    return bank.connect(":memory:")


@pytest.fixture
def two_accounts(conn):
    a = bank.create_account(conn, "Ada", "1234")
    b = bank.create_account(conn, "Bola", "4321")
    return conn, a, b


def test_deposit_increases_balance(two_accounts):
    conn, a, _ = two_accounts
    bank.deposit(conn, a, bank.to_kobo("500.50"))
    assert bank.get_balance(conn, a, "1234") == 50050


def test_withdraw_reduces_balance(two_accounts):
    conn, a, _ = two_accounts
    bank.deposit(conn, a, 10_000)
    bank.withdraw(conn, a, "1234", 4_000)
    assert bank.get_balance(conn, a, "1234") == 6_000


def test_cannot_overdraw(two_accounts):
    conn, a, _ = two_accounts
    bank.deposit(conn, a, 1_000)
    with pytest.raises(bank.BankError):
        bank.withdraw(conn, a, "1234", 2_000)
    assert bank.get_balance(conn, a, "1234") == 1_000


def test_wrong_pin_rejected(two_accounts):
    conn, a, _ = two_accounts
    bank.deposit(conn, a, 1_000)
    with pytest.raises(bank.BankError):
        bank.withdraw(conn, a, "0000", 500)


def test_transfer_moves_money(two_accounts):
    conn, a, b = two_accounts
    bank.deposit(conn, a, 10_000)
    bank.transfer(conn, a, "1234", b, 3_000)
    assert bank.get_balance(conn, a, "1234") == 7_000
    assert bank.get_balance(conn, b, "4321") == 3_000


def test_failed_transfer_changes_nothing(two_accounts):
    conn, a, b = two_accounts
    bank.deposit(conn, a, 1_000)
    with pytest.raises(bank.BankError):
        bank.transfer(conn, a, "1234", b, 5_000)
    assert bank.get_balance(conn, a, "1234") == 1_000
    assert bank.get_balance(conn, b, "4321") == 0


def test_invalid_amounts():
    for bad in ["0", "-5", "abc", "10.555"]:
        with pytest.raises(bank.BankError):
            bank.to_kobo(bad)


def test_pin_is_hashed(two_accounts):
    conn, a, _ = two_accounts
    row = conn.execute("SELECT pin_hash FROM accounts WHERE id = ?", (a,)).fetchone()
    assert "1234" not in row["pin_hash"]


def test_history_records_transactions(two_accounts):
    conn, a, b = two_accounts
    bank.deposit(conn, a, 5_000)
    bank.transfer(conn, a, "1234", b, 2_000)
    kinds = [r["kind"] for r in bank.history(conn, a, "1234")]
    assert kinds == ["transfer_out", "deposit"]
