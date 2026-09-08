import pytest
from app.blockchain.ethereum import EthereumProvider
from app.blockchain.parser import TransactionParser
from app.blockchain.cross_chain import CrossChainDetector

def test_ethereum_address_validation():
    provider = EthereumProvider(network="Sepolia")
    # Valid checksummed & lowercase addresses
    assert provider.validate_address("0x28C6c06298d514Db089934071355E5743bf21d60") is True
    assert provider.validate_address("0x28c6c06298d514db089934071355e5743bf21d60") is True
    # Invalid addresses
    assert provider.validate_address("0xInvalidHexAddress") is False
    assert provider.validate_address("12345") is False
    assert provider.validate_address("") is False

def test_transaction_normalization():
    raw_dict = {
        "transaction_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "block_number": 1234567,
        "timestamp": 1700000000,
        "from_address": "0x28c6c06298d514db089934071355e5743bf21d60",
        "to_address": "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
        "amount_native": 1.5,
        "gas_used": 21000,
        "gas_fee": 0.00042,
        "status": "SUCCESS"
    }
    normalized = TransactionParser.parse_dict(raw_dict, blockchain="Ethereum")
    assert normalized.transaction_hash == raw_dict["transaction_hash"]
    assert normalized.amount_native == 1.5
    assert normalized.amount_usd_if_available == 4500.0
    assert normalized.from_address.startswith("0x")
    assert normalized.status == "SUCCESS"

def test_cross_chain_bridge_detection():
    # Polygon bridge predicate address
    polygon_bridge = "0xa0c68c638235ee32657e8f720a23cec1bfc77c77"
    transition = CrossChainDetector.identify_bridge_interaction(
        to_address=polygon_bridge,
        from_address="0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97",
        tx_hash="0xabcd1234",
        amount=2.0,
        current_chain="Ethereum"
    )
    assert transition is not None
    assert transition.destination_blockchain == "Polygon"
    assert "Polygon" in transition.bridge_name
