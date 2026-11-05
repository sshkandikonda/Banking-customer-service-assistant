import json
from pathlib import Path

BANK_PATH = Path(__file__).resolve().parents[1] / "data" / "bank.json"


def list_customer_ids(path: Path = BANK_PATH) -> list[str]:
    return [customer["id"] for customer in _load(path)["customers"]]


def balance_enquiry(customer_id: str, path: Path = BANK_PATH) -> dict:
    customer = _customer(customer_id, path)
    return {
        "customer": customer["name"],
        "accounts": [
            {"ref": account["ref"], "type": account["type"], "balance": account["balance"]}
            for account in customer["accounts"]
        ],
    }


def transaction_details(
    customer_id: str,
    account_ref: str | None = None,
    description: str | None = None,
    path: Path = BANK_PATH,
) -> dict:
    accounts = _accounts(customer_id, account_ref, path)
    matches = []
    needle = (description or "").lower()
    for account in accounts:
        for txn in account["transactions"]:
            if needle and needle not in txn["description"].lower():
                continue
            matches.append({"account_ref": account["ref"], **txn})
    return {"transactions": matches}


def statement_request(
    customer_id: str,
    account_ref: str | None = None,
    path: Path = BANK_PATH,
) -> dict:
    accounts = _accounts(customer_id, account_ref, path)
    return {
        "statements": [
            {
                "account_ref": account["ref"],
                "type": account["type"],
                "balance": account["balance"],
                "transactions": account["transactions"],
            }
            for account in accounts
        ]
    }


def change_of_address(customer_id: str, new_address: str, path: Path = BANK_PATH) -> dict:
    address = new_address.strip()
    if not address:
        raise ValueError("An address is required.")
    data = _load(path)
    customer = _find(data, customer_id)
    customer["address"] = address
    _save(data, path)
    return {"saved": True, "address": address}


def cheque_book_request(
    customer_id: str,
    account_ref: str | None = None,
    leaves: int = 25,
    path: Path = BANK_PATH,
) -> dict:
    if leaves not in {25, 50}:
        raise ValueError("A cheque book can have 25 or 50 leaves.")
    data = _load(path)
    customer = _find(data, customer_id)
    account = _pick(customer, account_ref)
    request = {
        "id": f"cb_{len(customer['cheque_books']) + 1}",
        "account_ref": account["ref"],
        "leaves": leaves,
        "deliver_to": customer["address"],
        "status": "requested",
    }
    customer["cheque_books"].append(request)
    _save(data, path)
    return {"saved": True, "request": request}


def kyc_update(customer_id: str, kyc_status: str, path: Path = BANK_PATH) -> dict:
    status = kyc_status.strip().lower()
    if status not in {"pending", "verified"}:
        raise ValueError("KYC status must be pending or verified.")
    data = _load(path)
    customer = _find(data, customer_id)
    customer["kyc_status"] = status
    _save(data, path)
    return {"saved": True, "kyc_status": status}


def _accounts(customer_id: str, account_ref: str | None, path: Path) -> list[dict]:
    customer = _customer(customer_id, path)
    if account_ref is None:
        return customer["accounts"]
    return [_pick(customer, account_ref)]


def _customer(customer_id: str, path: Path) -> dict:
    return _find(_load(path), customer_id)


def _find(data: dict, customer_id: str) -> dict:
    for customer in data["customers"]:
        if customer["id"] == customer_id:
            return customer
    raise ValueError("Unknown customer.")


def _pick(customer: dict, account_ref: str | None) -> dict:
    accounts = customer["accounts"]
    if account_ref is None:
        if len(accounts) == 1:
            return accounts[0]
        refs = ", ".join(account["ref"] for account in accounts)
        raise ValueError(f"This customer has more than one account. Choose one of: {refs}.")
    for account in accounts:
        if account["ref"] == account_ref:
            return account
    raise ValueError("That account is not on this customer's profile.")


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _save(data: dict, path: Path) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")
