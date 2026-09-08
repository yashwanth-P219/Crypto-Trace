from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.blockchain.adapter import BlockchainAdapter, EVMAdapter
from app.config import settings

SUPPORTED_NETWORKS: Dict[int, Dict[str, Any]] = {
    11155111: {
        "chain_id": 11155111,
        "name": "Ethereum Sepolia",
        "symbol": "ETH",
        "is_evm": True,
        "is_active": True,
        "is_testnet": True,
        "rpc_url_configured": True,
        "explorer_url": "https://sepolia.etherscan.io"
    },
    1: {
        "chain_id": 1,
        "name": "Ethereum Mainnet",
        "symbol": "ETH",
        "is_evm": True,
        "is_active": True,
        "is_testnet": False,
        "rpc_url_configured": False,
        "explorer_url": "https://etherscan.io"
    },
    137: {
        "chain_id": 137,
        "name": "Polygon PoS",
        "symbol": "POL",
        "is_evm": True,
        "is_active": True,
        "is_testnet": False,
        "rpc_url_configured": False,
        "explorer_url": "https://polygonscan.com"
    },
    56: {
        "chain_id": 56,
        "name": "BNB Smart Chain",
        "symbol": "BNB",
        "is_evm": True,
        "is_active": True,
        "is_testnet": False,
        "rpc_url_configured": False,
        "explorer_url": "https://bscscan.com"
    }
}

class ChainRegistry:
    _adapters: Dict[int, BlockchainAdapter] = {}

    @classmethod
    def list_chains(cls) -> List[Dict[str, Any]]:
        return list(SUPPORTED_NETWORKS.values())

    @classmethod
    def is_supported(cls, chain_id: int) -> bool:
        return chain_id in SUPPORTED_NETWORKS

    @classmethod
    def get_chain(cls, chain_id: int) -> Dict[str, Any]:
        if chain_id not in SUPPORTED_NETWORKS:
            supported = list(SUPPORTED_NETWORKS.keys())
            raise ValueError(
                f"Unsupported blockchain network chain_id={chain_id}. "
                f"Supported chain IDs are: {supported}."
            )
        return SUPPORTED_NETWORKS[chain_id]

    @classmethod
    def get_adapter(cls, chain_id: int) -> BlockchainAdapter:
        info = cls.get_chain(chain_id)
        if chain_id not in cls._adapters:
            rpc_map = {
                11155111: settings.SEPOLIA_RPC_URL,
                1: settings.ETHEREUM_RPC_URL,
                137: settings.POLYGON_RPC_URL,
                56: settings.BNB_RPC_URL
            }
            rpc_url = rpc_map.get(chain_id, settings.SEPOLIA_RPC_URL)
            cls._adapters[chain_id] = EVMAdapter(
                chain_id=chain_id,
                name=info["name"],
                symbol=info["symbol"],
                rpc_url=rpc_url
            )
        return cls._adapters[chain_id]

    @classmethod
    def seed_db_networks(cls, db: Session):
        from app.database.models import BlockchainNetwork
        for chain_id, data in SUPPORTED_NETWORKS.items():
            existing = db.query(BlockchainNetwork).filter(BlockchainNetwork.chain_id == chain_id).first()
            if not existing:
                net = BlockchainNetwork(
                    chain_id=chain_id,
                    name=data["name"],
                    symbol=data["symbol"],
                    is_active=data["is_active"],
                    is_evm=data["is_evm"],
                    rpc_url_configured=data["rpc_url_configured"],
                    explorer_url=data["explorer_url"]
                )
                db.add(net)
        db.commit()
