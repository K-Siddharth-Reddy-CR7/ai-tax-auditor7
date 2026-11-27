"""The original implementation and datasets must stay byte-identical to main@01dde8b."""
import hashlib
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ORIGINAL_SHA256 = {
    "backend/server.py": "a4bffa5f17a20286c08f4eae4d1a2e05eb312360975b2a1d459314a057e9ae7b",
    "products.json": "380c6f8132abc924e17bab8ea824d4d945f8eabc549cb7c0f91cad1e8f27a9cf",
    "taxes.json": "d759029228fbe7beeb00cbd31add09ad699d9492d96422aebcd5d63e63bdf8a5",
    "trade_policies.json": "ca1f21d13ed372675fd9be593dc73147d36e0d0fa65c1ea72c0824ffdf06775b",
    "sample_transactions.json": "cc94509f0bea6b4fe58d898164f80d6a2b681a45bc121df889fd740b25e1e70d",
    "products.csv": "9656ad0707dc8202449e9fd90c9512adf9a85eeddc83d553a108d83e27cba5e8",
    "taxes.csv": "0a256dbcf63d4ac6da3177d9cf65da301f40d5888904e3db7c2b9732ee5660cb",
    "trade_policies.csv": "00d4beb5822666c19a936f61c171a5ef4fa636b386901711f2eec1425fb67636",
    "sample_transactions.csv": "aab9b0be815ab3e43fa51e55f623ac0ab6a2746cdb1ffc72ca2b178658c2f3b8",
    "Majorpro (1).ipynb": "985cc95989b9c1f89600b2f01d06fddf66f330da009568b33ed0d95153f02298",
    "backend/requirements.txt": "be3345c0562804d5cdeb8b75384cb32154c32e88bbb6c8e0a620a181c0be298a",
}


@pytest.mark.parametrize("rel,expected", sorted(ORIGINAL_SHA256.items()))
def test_original_file_unchanged(rel, expected):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        assert hashlib.sha256(fh.read()).hexdigest() == expected
