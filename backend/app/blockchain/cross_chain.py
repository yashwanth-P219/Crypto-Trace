from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class CrossChainTransition(BaseModel):
    source_blockchain: str
    destination_blockchain: str
    bridge_name: str
    bridge_contract_address: str
    source_tx_hash: str
    estimated_amount: float
    confidence: str = "HIGH"

# Canonical Bridge Contract Registry
KNOWN_BRIDGE_CONTRACTS = {
    # Polygon PoS Bridge
    "0xa0c68c638235ee32657e8f720a23cec1bfc77c77": {
        "name": "Polygon PoS Bridge: ERC20 Predicate",
        "source": "Ethereum",
        "destination": "Polygon"
    },
    "0x401f6c983ea34274ec46f84d70b31c151321188b": {
        "name": "Polygon PoS Bridge: Ether Predicate",
        "source": "Ethereum",
        "destination": "Polygon"
    },
    # Binance Bridge / Anyswap / Multichain
    "0xd1235d9472e3a89e900994f31c257850df3ba61e": {
        "name": "Binance Official Bridge",
        "source": "Ethereum",
        "destination": "BNB Smart Chain"
    },
    # Stargate Finance Router
    "0x8731d54e9d02c271b964a500ad58ebb9ab49cc36": {
        "name": "Stargate Finance Router",
        "source": "Multi-Chain",
        "destination": "Multi-Chain"
    },
    # Across Protocol SpokePool
    "0x5c7bcabfe500223703c3732b130089853a483a8b": {
        "name": "Across Protocol SpokePool",
        "source": "Ethereum",
        "destination": "Polygon/Arbitrum/Optimism"
    }
}

class CrossChainDetector:
    @staticmethod
    def identify_bridge_interaction(to_address: str, from_address: str, tx_hash: str, amount: float, current_chain: str) -> Optional[CrossChainTransition]:
        norm_to = to_address.lower() if to_address else ""
        if norm_to in KNOWN_BRIDGE_CONTRACTS:
            info = KNOWN_BRIDGE_CONTRACTS[norm_to]
            dest = info["destination"]
            if dest == current_chain:
                dest = "Polygon" if current_chain == "Ethereum" else "Ethereum"
            return CrossChainTransition(
                source_blockchain=current_chain,
                destination_blockchain=dest,
                bridge_name=info["name"],
                bridge_contract_address=norm_to,
                source_tx_hash=tx_hash,
                estimated_amount=amount,
                confidence="HIGH"
            )
        return None

    @staticmethod
    def get_known_bridges() -> List[Dict[str, Any]]:
        return [
            {"address": addr, **meta}
            for addr, meta in KNOWN_BRIDGE_CONTRACTS.items()
        ]
