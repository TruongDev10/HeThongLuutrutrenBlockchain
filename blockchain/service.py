import json
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from config import (
    BASE_DIR,
    BLOCKCHAIN_ACCOUNT_ADDRESS,
    BLOCKCHAIN_CHAIN_ID,
    BLOCKCHAIN_CONTRACT_ADDRESS,
    BLOCKCHAIN_ENABLED,
    BLOCKCHAIN_PRIVATE_KEY,
    BLOCKCHAIN_PROVIDER_URI,
    BLOCKCHAIN_TIMEOUT_SECONDS,
)
from database.init_db import update_blockchain_result


ABI_PATH = BASE_DIR / "blockchain" / "abi" / "ProductClassificationLedger.json"
SETTINGS_PATH = BASE_DIR / "blockchain" / "blockchain_settings.json"
COMPATIBLE_ADD_RECORD_ABI = {
    "inputs": [
        {"internalType": "string", "name": "_objectName", "type": "string"},
        {"internalType": "string", "name": "_detectedColor", "type": "string"},
        {"internalType": "uint256", "name": "_confidence", "type": "uint256"},
        {"internalType": "string", "name": "_status", "type": "string"},
        {"internalType": "string", "name": "_resultHash", "type": "string"},
    ],
    "name": "addRecord",
    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
    "stateMutability": "nonpayable",
    "type": "function",
}


@dataclass
class BlockchainJob:
    log_id: int
    product_id: str
    object_name: str
    color: str
    result: str
    rgb_value: str
    hsv_value: str
    timestamp_iso: str
    confidence: int = 0
    result_hash: str = ""


class BlockchainLedger:
    def __init__(self):
        self.enabled = BLOCKCHAIN_ENABLED
        self.provider_uri = BLOCKCHAIN_PROVIDER_URI
        self.contract_address = BLOCKCHAIN_CONTRACT_ADDRESS
        self.private_key = BLOCKCHAIN_PRIVATE_KEY
        self.account_address = BLOCKCHAIN_ACCOUNT_ADDRESS
        self.chain_id = BLOCKCHAIN_CHAIN_ID
        self.status_message = "not initialized"
        self.last_tx_hash = None
        self._web3 = None
        self._contract = None
        self._load_local_settings()
        self._queue = queue.Queue(maxsize=500)
        self._worker = threading.Thread(target=self._run_worker, daemon=True)
        self._worker.start()
        self._connect()

    def configure(self, provider_uri=None, contract_address=None, account_address=None, private_key=None, chain_id=None):
        if provider_uri is not None:
            self.provider_uri = self._normalize_provider_uri(provider_uri)
        if contract_address is not None:
            self.contract_address = contract_address.strip()
        if account_address is not None:
            self.account_address = account_address.strip()
        if private_key is not None:
            self.private_key = private_key.strip()
        if chain_id:
            self.chain_id = int(chain_id)
        self._connect()
        self._save_local_settings()

    def _load_local_settings(self):
        if not SETTINGS_PATH.exists():
            return
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            self.provider_uri = self._normalize_provider_uri(data.get("provider_uri") or self.provider_uri)
            self.chain_id = int(data.get("chain_id") or self.chain_id)
        except Exception:
            return

    def _save_local_settings(self):
        try:
            SETTINGS_PATH.write_text(
                json.dumps(
                    {
                        "provider_uri": self.provider_uri,
                        "chain_id": self.chain_id,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _normalize_provider_uri(self, provider_uri):
        uri = (provider_uri or "").strip()
        if not uri:
            return self.provider_uri
        if uri.startswith("http//"):
            uri = "http://" + uri[len("http//") :]
        elif uri.startswith("https//"):
            uri = "https://" + uri[len("https//") :]
        elif "://" not in uri:
            uri = f"http://{uri}"
        return uri

    def _connect(self):
        if not self.enabled:
            self.status_message = "disabled"
            self._web3 = None
            self._contract = None
            return
        if not self.contract_address:
            self.status_message = "not configured: missing contract address"
            self._web3 = None
            self._contract = None
            return
        try:
            from web3 import Web3

            parsed_provider = urlparse(self.provider_uri)
            if parsed_provider.scheme not in {"http", "https"} or not parsed_provider.hostname:
                self.status_message = "Loi: Ganache RPC khong hop le, dung dang http://127.0.0.1:7545"
                self._web3 = None
                self._contract = None
                return
            self._web3 = Web3(Web3.HTTPProvider(self.provider_uri, request_kwargs={"timeout": BLOCKCHAIN_TIMEOUT_SECONDS}))
            if not self._web3.is_connected():
                self.status_message = f"Loi: Ganache RPC chua mo tai {self.provider_uri}"
                self._contract = None
                return
            abi = json.loads(Path(ABI_PATH).read_text(encoding="utf-8"))
            if not any(item.get("name") == "addRecord" and len(item.get("inputs", [])) == 5 for item in abi):
                abi.append(COMPATIBLE_ADD_RECORD_ABI)
            if not self._web3.is_address(self.contract_address):
                self._contract = None
                self.status_message = "Loi: contract address khong hop le"
                return
            if self.account_address and not self._web3.is_address(self.account_address):
                self._contract = None
                self.status_message = "Loi: account address khong hop le"
                return
            checksum_address = self._web3.to_checksum_address(self.contract_address)
            if len(self._web3.eth.get_code(checksum_address)) == 0:
                self._contract = None
                if self._web3.eth.block_number == 0:
                    self.status_message = (
                        "Ganache da ket noi OK, nhung chua co contract nao tren Ganache. "
                        "Hay deploy contract lai bang Remix Environment ket noi http://127.0.0.1:7545."
                    )
                else:
                    self.status_message = "Ganache da ket noi OK, nhung contract address nay khong nam tren Ganache hien tai."
                return
            self._contract = self._web3.eth.contract(address=checksum_address, abi=abi)
            self._contract.functions.totalRecords().call()
            current_accounts = [self._web3.to_checksum_address(account) for account in self._web3.eth.accounts]
            if self.private_key:
                key_account = self._web3.eth.account.from_key(self.private_key).address
                if self.account_address:
                    checksum_account = self._web3.to_checksum_address(self.account_address)
                    if checksum_account != key_account:
                        self._contract = None
                        self.status_message = "Loi: private key khong khop account address"
                        return
                    self.account_address = checksum_account
                else:
                    self.account_address = key_account
            else:
                if not current_accounts:
                    self._contract = None
                    self.status_message = "Loi: Ganache khong co account dang mo khoa"
                    return
                self.account_address = current_accounts[0]
            self.status_message = "Ket noi thanh cong"
        except Exception as exc:
            self._contract = None
            self.status_message = f"Loi: {exc}"

    def enqueue(self, job: BlockchainJob):
        if not self.ready:
            update_blockchain_result(job.log_id, None, self.status_message)
            return False
        try:
            self._queue.put_nowait(job)
            update_blockchain_result(job.log_id, None, "queued")
            return True
        except queue.Full:
            update_blockchain_result(job.log_id, None, "queue full")
            return False

    @property
    def ready(self):
        return bool(
            self.enabled
            and self._web3 is not None
            and self._contract is not None
            and self._web3.is_connected()
        )

    def get_status(self):
        total_records = self.get_total_records()
        diagnostics = self._diagnostics()
        return {
            "enabled": self.enabled,
            "ready": self.ready,
            "provider_uri": self.provider_uri,
            "chain_id": self.chain_id,
            "contract_address": self.contract_address,
            "account_address": self.account_address,
            "status": self.status_message,
            "queue_size": self._queue.qsize(),
            "last_tx_hash": self.last_tx_hash,
            "total_records": total_records,
            "totalRecords": total_records,
            "records_on_chain": total_records,
            "diagnostics": diagnostics,
        }

    def get_total_records(self):
        if not self.ready:
            self._connect()
        if not self.ready:
            return None
        try:
            total_records = int(self._contract.functions.totalRecords().call())
            self.status_message = "Ket noi thanh cong"
            return total_records
        except Exception as exc:
            self.status_message = f"Loi doc totalRecords(): {exc}"
            return None

    def _diagnostics(self):
        details = {
            "rpc_connected": False,
            "chain_id": None,
            "block_number": None,
            "accounts": [],
            "contract_code_size": 0,
            "contract_deployed": False,
            "account_unlocked": False,
        }
        try:
            from web3 import Web3

            web3 = self._web3 or Web3(
                Web3.HTTPProvider(self.provider_uri, request_kwargs={"timeout": BLOCKCHAIN_TIMEOUT_SECONDS})
            )
            details["rpc_connected"] = web3.is_connected()
            if not details["rpc_connected"]:
                return details
            details["chain_id"] = web3.eth.chain_id
            details["block_number"] = web3.eth.block_number
            details["accounts"] = web3.eth.accounts
            if self.contract_address:
                if not web3.is_address(self.contract_address):
                    details["error"] = "invalid contract address"
                    return details
                checksum_address = web3.to_checksum_address(self.contract_address)
                code_size = len(web3.eth.get_code(checksum_address))
                details["contract_code_size"] = code_size
                details["contract_deployed"] = code_size > 0
            if self.private_key and self.account_address:
                checksum_account = web3.to_checksum_address(self.account_address)
                details["account_unlocked"] = checksum_account in web3.eth.accounts
            else:
                details["account_unlocked"] = bool(web3.eth.accounts)
        except Exception as exc:
            details["error"] = str(exc)
        return details

    def _run_worker(self):
        while True:
            job = self._queue.get()
            try:
                tx_hash = self._send_transaction(job)
                self.last_tx_hash = tx_hash
                update_blockchain_result(job.log_id, tx_hash, "confirmed")
            except Exception as exc:
                update_blockchain_result(job.log_id, None, f"failed: {exc}")
                self.status_message = f"tx failed: {exc}"
            finally:
                self._queue.task_done()

    def _send_transaction(self, job: BlockchainJob):
        if not self.ready:
            raise RuntimeError(self.status_message)
        timestamp = int(datetime.fromisoformat(job.timestamp_iso).timestamp())
        sender = self.account_address
        if self.private_key:
            if not sender:
                sender = self._web3.eth.account.from_key(self.private_key).address
                self.account_address = sender
        else:
            accounts = self._web3.eth.accounts
            if not accounts:
                raise RuntimeError("missing Ganache account")
            current_accounts = [self._web3.to_checksum_address(account) for account in accounts]
            if not sender or self._web3.to_checksum_address(sender) not in current_accounts:
                sender = current_accounts[0]
                self.account_address = sender

        function_call = self._select_add_record_function(job, sender, timestamp)

        tx = function_call.build_transaction(
            {
                "from": sender,
                "nonce": self._web3.eth.get_transaction_count(sender),
                "chainId": self.chain_id,
                "gas": 450000,
                "gasPrice": self._web3.eth.gas_price,
            }
        )

        if self.private_key:
            signed = self._web3.eth.account.sign_transaction(tx, private_key=self.private_key)
            tx_hash = self._web3.eth.send_raw_transaction(signed.raw_transaction)
        else:
            tx_hash = self._web3.eth.send_transaction(tx)

        receipt = self._web3.eth.wait_for_transaction_receipt(tx_hash, timeout=BLOCKCHAIN_TIMEOUT_SECONDS)
        if receipt.status != 1:
            raise RuntimeError("transaction reverted")
        return tx_hash.hex()

    def _select_add_record_function(self, job, sender, timestamp):
        candidates = [
            self._contract.functions.addRecord(
                job.product_id,
                job.object_name,
                job.color,
                job.result,
                job.rgb_value,
                job.hsv_value,
                int(job.confidence),
                job.result_hash,
                timestamp,
            ),
            self._contract.functions.addRecord(
                job.object_name,
                job.color,
                int(job.confidence),
                job.result,
                job.result_hash,
            ),
        ]
        last_error = None
        for function_call in candidates:
            try:
                function_call.call({"from": sender})
                return function_call
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"contract ABI mismatch: addRecord khong khop hop dong da deploy ({last_error})")


ledger = BlockchainLedger()
