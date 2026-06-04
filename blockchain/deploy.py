import json
import os
from pathlib import Path

from solcx import compile_standard, get_installed_solc_versions, install_solc
from web3 import Web3

from config import BASE_DIR


CONTRACT_PATH = BASE_DIR / "blockchain" / "contracts" / "ProductClassificationLedger.sol"
ABI_PATH = BASE_DIR / "blockchain" / "abi" / "ProductClassificationLedger.json"
SETTINGS_PATH = BASE_DIR / "blockchain" / "blockchain_settings.json"
SOLCX_DIR = BASE_DIR / ".solcx"
SOLC_VERSION = "0.8.20"


def deploy_product_classification_contract(
    provider_uri="http://127.0.0.1:7545",
    private_key="",
    account_address="",
    chain_id=1337,
):
    web3 = Web3(Web3.HTTPProvider(provider_uri))
    if not web3.is_connected():
        raise RuntimeError(f"Cannot connect to {provider_uri}. Start Ganache first.")

    source = CONTRACT_PATH.read_text(encoding="utf-8")
    SOLCX_DIR.mkdir(parents=True, exist_ok=True)
    installed_versions = get_installed_solc_versions(solcx_binary_path=SOLCX_DIR)
    if SOLC_VERSION not in {str(version) for version in installed_versions}:
        install_solc(SOLC_VERSION, solcx_binary_path=SOLCX_DIR)

    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": {"ProductClassificationLedger.sol": {"content": source}},
            "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}},
        },
        solc_version=SOLC_VERSION,
        solc_binary=SOLCX_DIR / f"solc-v{SOLC_VERSION}",
    )
    contract_data = compiled["contracts"]["ProductClassificationLedger.sol"]["ProductClassificationLedger"]
    abi = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]
    ABI_PATH.write_text(json.dumps(abi, indent=2), encoding="utf-8")

    if private_key:
        sender = web3.eth.account.from_key(private_key).address
    elif account_address:
        sender = web3.to_checksum_address(account_address)
    else:
        accounts = web3.eth.accounts
        if not accounts:
            raise RuntimeError("Ganache has no unlocked account.")
        sender = web3.to_checksum_address(accounts[0])

    contract = web3.eth.contract(abi=abi, bytecode=bytecode)
    tx = contract.constructor().build_transaction(
        {
            "from": sender,
            "nonce": web3.eth.get_transaction_count(sender),
            "chainId": int(chain_id),
            "gas": 2200000,
            "gasPrice": web3.eth.gas_price,
        }
    )

    if private_key:
        signed = web3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    else:
        tx_hash = web3.eth.send_transaction(tx)

    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status != 1:
        raise RuntimeError("Contract deployment reverted.")

    settings = {
        "provider_uri": provider_uri,
        "contract_address": receipt.contractAddress,
        "account_address": sender,
        "chain_id": int(chain_id),
    }
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return {
        **settings,
        "tx_hash": tx_hash.hex(),
        "settings_path": os.fspath(SETTINGS_PATH),
    }
