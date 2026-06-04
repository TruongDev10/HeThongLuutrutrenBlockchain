import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, os.fspath(ROOT))

from blockchain.deploy import deploy_product_classification_contract


def main():
    provider_uri = os.getenv("BLOCKCHAIN_PROVIDER_URI", "http://127.0.0.1:7545")
    private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY", "")
    account_address = os.getenv("BLOCKCHAIN_ACCOUNT_ADDRESS", "")
    chain_id = int(os.getenv("BLOCKCHAIN_CHAIN_ID", "1337"))

    deployment = deploy_product_classification_contract(
        provider_uri=provider_uri,
        private_key=private_key,
        account_address=account_address,
        chain_id=chain_id,
    )
    print("Contract deployed")
    print(f"Address: {deployment['contract_address']}")
    print(f"Tx hash: {deployment['tx_hash']}")
    print(f"Settings saved: {deployment['settings_path']}")
    print("Set environment variable before running app:")
    print(f"set BLOCKCHAIN_CONTRACT_ADDRESS={deployment['contract_address']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
