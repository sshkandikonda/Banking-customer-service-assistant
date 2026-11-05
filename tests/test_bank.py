import json
import tempfile
import unittest
from pathlib import Path

from app.bank import balance_enquiry, cheque_book_request, transaction_details


class BankToolTests(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve().parents[1] / "data" / "bank.json"
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "bank.json"
        self.path.write_text(source.read_text())

    def tearDown(self):
        self.directory.cleanup()

    def test_balance_uses_the_customer_from_the_caller(self):
        result = balance_enquiry("cust_101", self.path)
        self.assertEqual(result["accounts"][0]["ref"], "acc_1")
        self.assertEqual(result["accounts"][0]["balance"], 84250.75)

    def test_transaction_search_finds_a_debit(self):
        result = transaction_details("cust_103", description="unknown", path=self.path)
        self.assertEqual(len(result["transactions"]), 1)
        self.assertEqual(result["transactions"][0]["amount"], -890.0)

    def test_cheque_book_is_saved_to_the_registered_address(self):
        result = cheque_book_request("cust_103", path=self.path)
        saved = json.loads(self.path.read_text())
        customer = next(item for item in saved["customers"] if item["id"] == "cust_103")
        self.assertEqual(result["request"]["deliver_to"], "22 Beach Road, Kochi")
        self.assertEqual(customer["cheque_books"][0]["account_ref"], "acc_4")


if __name__ == "__main__":
    unittest.main()
