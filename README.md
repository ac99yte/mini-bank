# Mini Bank

A command-line banking system built with Python and SQLite. It supports creating accounts, deposits, withdrawals, transfers between accounts, balance checks and transaction history.

## Why I built it

I wanted to understand how real banking software keeps money safe and accurate, so I focused on three things banks care about:

- **Atomic transfers:** both sides of a transfer succeed together or the whole thing is rolled back, so money is never lost or duplicated.
- **Secure PINs:** PINs are salted and hashed with PBKDF2, never stored in plain text.
- **Exact money handling:** amounts are stored as integer kobo, not floats, to avoid rounding errors.

## Features

- Create accounts with a 4-digit PIN
- Deposit, withdraw and transfer funds
- Balance checks and full transaction history
- Input validation (no negative amounts, no overdrafts, no transfers to yourself)
- Unit tests with pytest

## Run it

```bash
git clone https://github.com/ac99yte/mini-bank.git
cd mini-bank
pip install -r requirements.txt
python main.py
```

## Run the tests

```bash
pytest
```

## Project structure

```
bank.py        # core logic and database (SQLite)
main.py        # command-line menu
test_bank.py   # pytest unit tests
```

## Possible next steps

- REST API with Flask
- Deploy on AWS
- Fraud-detection rules on transaction data
