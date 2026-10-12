"""Core banking logic: accounts, deposits, withdrawals and atomic transfers.

Money is stored as integer kobo (1 naira = 100 kobo) to avoid float rounding errors.
"""
import hashlib
import hmac
import os
import sqlite3
from decimal import Decimal, InvalidOperation

DB_PATH = "bank.db"


class BankError(Exception):
    """Raised for any rule violation (bad PIN, low balance, invalid amount...)."""


def connect(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pin_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0 CHECK (balance >= 0)
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL REFERENCES accounts(id),
            kind TEXT NOT NULL,
            amount INTEGER NOT NULL,
            related_account_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    return conn


def to_kobo(value):
    """Convert a naira amount like '1500.50' to integer kobo."""
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        raise BankError("Amount must be a number.")
    if amount <= 0:
        raise BankError("Amount must be greater than zero.")
    if amount != amount.quantize(Decimal("0.01")):
        raise BankError("Amount cannot have more than 2 decimal places.")
    return int(amount * 100)


def _hash_pin(pin, salt):
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 100_000).hex()


def create_account(conn, name, pin):
    if not name.strip():
        raise BankError("Name cannot be empty.")
    if not (pin.isdigit() and len(pin) == 4):
        raise BankError("PIN must be exactly 4 digits.")
    salt = os.urandom(16)
    with conn:
        cur = conn.execute(
            "INSERT INTO accounts (name, pin_hash, salt) VALUES (?, ?, ?)",
            (name.strip(), _hash_pin(pin, salt), salt.hex()),
        )
    return cur.lastrowid


def _get_account(conn, account_id):
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row is None:
        raise BankError(f"Account {account_id} does not exist.")
    return row


def _check_pin(account, pin):
    expected = account["pin_hash"]
    actual = _hash_pin(pin, bytes.fromhex(account["salt"]))
    if not hmac.compare_digest(expected, actual):
        raise BankError("Incorrect PIN.")


def get_balance(conn, account_id, pin):
    account = _get_account(conn, account_id)
    _check_pin(account, pin)
    return account["balance"]


def deposit(conn, account_id, amount_kobo):
    _get_account(conn, account_id)
    with conn:
        conn.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (amount_kobo, account_id),
        )
        conn.execute(
            "INSERT INTO transactions (account_id, kind, amount) VALUES (?, 'deposit', ?)",
            (account_id, amount_kobo),
        )


def withdraw(conn, account_id, pin, amount_kobo):
    account = _get_account(conn, account_id)
    _check_pin(account, pin)
    if account["balance"] < amount_kobo:
        raise BankError("Insufficient funds.")
    with conn:
        conn.execute(
            "UPDATE accounts SET balance = balance - ? WHERE id = ?",
            (amount_kobo, account_id),
        )
        conn.execute(
            "INSERT INTO transactions (account_id, kind, amount) VALUES (?, 'withdrawal', ?)",
            (account_id, amount_kobo),
        )


def transfer(conn, from_id, pin, to_id, amount_kobo):
    """Move money between accounts. Atomic: both updates succeed or neither does."""
    if from_id == to_id:
        raise BankError("Cannot transfer to the same account.")
    sender = _get_account(conn, from_id)
    _get_account(conn, to_id)
    _check_pin(sender, pin)
    if sender["balance"] < amount_kobo:
        raise BankError("Insufficient funds.")
    # `with conn` commits on success and rolls back everything if any statement fails.
    with conn:
        conn.execute(
            "UPDATE accounts SET balance = balance - ? WHERE id = ?",
            (amount_kobo, from_id),
        )
        conn.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (amount_kobo, to_id),
        )
        conn.execute(
            "INSERT INTO transactions (account_id, kind, amount, related_account_id) "
            "VALUES (?, 'transfer_out', ?, ?)",
            (from_id, amount_kobo, to_id),
        )
        conn.execute(
            "INSERT INTO transactions (account_id, kind, amount, related_account_id) "
            "VALUES (?, 'transfer_in', ?, ?)",
            (to_id, amount_kobo, from_id),
        )


def history(conn, account_id, pin):
    account = _get_account(conn, account_id)
    _check_pin(account, pin)
    return conn.execute(
        "SELECT kind, amount, related_account_id, created_at FROM transactions "
        "WHERE account_id = ? ORDER BY id DESC",
        (account_id,),
    ).fetchall()
