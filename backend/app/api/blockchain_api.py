import logging
from fastapi import APIRouter
from app.blockchain.ethereum import EthereumProvider

logger = logging.getLogger("api.blockchain")
router = APIRouter(tags=["Blockchain Real-Time Status"])

provider = EthereumProvider(network="Sepolia")

@router.get("/blockchain/status")
def get_blockchain_status():
    """
    Returns real-time Ethereum Sepolia RPC connection status and latest block height.
    """
    try:
        status_data = provider.get_status()
        logger.info(f"Blockchain status checked: connected={status_data['connected']}, block={status_data['latest_block']}")
        return status_data
    except Exception as e:
        logger.error(f"Error querying blockchain status: {e}")
        return {
            "connected": False,
            "network": "Ethereum Sepolia",
            "latest_block": None,
            "error": str(e)
        }

@router.get("/blockchain/latest-block")
def get_latest_block():
    """
    Returns full block metadata for the latest mined block on Ethereum Sepolia.
    """
    try:
        block = provider.get_latest_block()
        if block:
            # Clean hexbytes for JSON serialization
            cleaned = {}
            for k, v in block.items():
                if hasattr(v, "hex"):
                    cleaned[k] = v.hex()
                elif isinstance(v, bytes):
                    cleaned[k] = "0x" + v.hex()
                elif isinstance(v, list):
                    cleaned[k] = [x.hex() if hasattr(x, "hex") else str(x) for x in v]
                else:
                    cleaned[k] = v
            return cleaned
        return {"error": "Block not available"}
    except Exception as e:
        logger.error(f"Error querying latest block: {e}")
        return {
            "error": f"Failed to retrieve block: {str(e)}"
        }

