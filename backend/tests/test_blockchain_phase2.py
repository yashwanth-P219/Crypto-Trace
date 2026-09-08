import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.blockchain.ethereum import EthereumProvider
from app.blockchain.rpc import ResilientRPCClient

client = TestClient(app)

# 1. Address Validation Tests
def test_address_validation_valid():
    provider = EthereumProvider(network="Sepolia")
    # Valid checksummed address
    assert provider.validate_address("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045") is True
    # Valid lowercase address
    assert provider.validate_address("0xd8da6bf26964af9d7eed9e03e53415d37aa96045") is True
    # Valid standard 20-byte EVM address
    assert provider.validate_address("0x71C7656EC7ab88b098defB751B7401B5f6d8976F") is True

def test_address_validation_invalid():
    provider = EthereumProvider(network="Sepolia")
    # Missing 0x prefix
    assert provider.validate_address("d8da6bf26964af9d7eed9e03e53415d37aa96045") is False
    # Invalid length (too short)
    assert provider.validate_address("0xd8da6bf26964af9d7eed9e03e53415d37aa96") is False
    # Invalid length (too long)
    assert provider.validate_address("0xd8da6bf26964af9d7eed9e03e53415d37aa96045ff12") is False
    # Non-hex characters
    assert provider.validate_address("0xZZZa6bf26964af9d7eed9e03e53415d37aa96045") is False
    # None and empty
    assert provider.validate_address("") is False
    assert provider.validate_address(None) is False

# 2. RPC Connection & Status Tests
def test_sepolia_provider_status():
    provider = EthereumProvider(network="Sepolia")
    status = provider.get_status()
    assert "connected" in status
    assert status["network"] == "Ethereum Sepolia"
    if status["connected"]:
        assert isinstance(status["latest_block"], int)
        assert status["latest_block"] > 0

def test_api_blockchain_status():
    response = client.get("/blockchain/status")
    assert response.status_code == 200
    data = response.json()
    assert "connected" in data
    assert data["network"] == "Ethereum Sepolia"
    assert "latest_block" in data
    # Also verify under /api/blockchain/status
    api_resp = client.get("/api/blockchain/status")
    assert api_resp.status_code == 200
    assert api_resp.json()["network"] == "Ethereum Sepolia"

# 3. Wallet Balance & Validation Endpoint Tests
def test_api_wallet_balance_valid():
    # Known test address
    addr = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
    response = client.get(f"/wallets/{addr}/balance")
    assert response.status_code == 200
    data = response.json()
    assert data["network"] == "Ethereum Sepolia"
    assert "balance" in data
    assert "balance_eth" in data
    assert data["address"].lower() == addr.lower()

def test_api_wallet_balance_invalid_address():
    bad_addr = "0xInvalidWalletAddress123"
    response = client.get(f"/wallets/{bad_addr}/balance")
    assert response.status_code == 400
    data = response.json()
    assert data == {"error": "Invalid Ethereum wallet address"}

# 4. Transaction Retrieval & 404 Tests
def test_api_transaction_not_found():
    non_existent_tx = "0x000000000000000000000000000000000000000000000000000000000000dead"
    response = client.get(f"/transactions/{non_existent_tx}")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data or "detail" in data

def test_api_transaction_valid_retrieval_or_db():
    # Test indexed transaction from DB or live block
    response = client.get("/transactions/0x1a2b3c4d5e6f708192a1b2c3d4e5f60718293a4b5c6d7e8f9012345678abcdef")
    if response.status_code == 200:
        data = response.json()
        assert "transaction_hash" in data
        assert "from_address" in data
        assert "to_address" in data
        assert "value" in data
        assert "status" in data

# 5. Resilient Error Handling Tests
def test_resilient_rpc_invalid_endpoint():
    # ResilientRPCClient must not crash when given a failing RPC endpoint
    client_resilient = ResilientRPCClient(
        primary_rpc_url="https://invalid-non-existent-domain-xyz.com",
        fallback_rpc_urls=["https://another-invalid-rpc-node.org"],
        max_retries=1,
        timeout=1
    )
    assert client_resilient.is_connected() is False
    assert client_resilient.get_latest_block_number() is None
    assert client_resilient.get_raw_balance("0xd8da6bf26964af9d7eed9e03e53415d37aa96045") == 0

# 6. Health Check Tests
def test_health_check():
    resp1 = client.get("/health")
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "healthy"
    
    resp2 = client.get("/api/health")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "healthy"
