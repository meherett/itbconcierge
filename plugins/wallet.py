from decimal import Decimal
from json import loads

from eth_wallet import Wallet
from eth_typing import URI
from web3 import Web3, WebsocketProvider

from slackbot_settings import (CLIENT_API_URL, CONTRACT_ADDRESS,
                               ITB_FOUNDATION_MNEMONIC)

from .model import Symbol


class WalletController:
    """
    ウォレットを制御するクラス
    """

    def __init__(self, address: str, privkey: str):
        self._address = address
        self._privkey = privkey
        self._web3 = Web3(WebsocketProvider(endpoint_uri=URI(CLIENT_API_URL)))
        checked_contract_address = self._web3.toChecksumAddress(CONTRACT_ADDRESS)
        abi = loads(ABI)
        self._contract = self._web3.eth.contract(abi=abi, address=checked_contract_address)

    @staticmethod
    def create_address(path=ITB_FOUNDATION_MNEMONIC["path"]) -> tuple:
        """
        新規アドレスを発行します。
        Parameters
        ----------
        path : str
            HDウォレットパス

        Returns
        -------
        tuple
            新規発行したアドレスと秘密鍵を返す。
            (new_address, new_privkey)
        """
        wallet = Wallet().from_mnemonic(
            mnemonic=ITB_FOUNDATION_MNEMONIC["mnemonic"],
            passphrase=ITB_FOUNDATION_MNEMONIC["passphrase"]
        )
        wallet.from_path(path=path)
        return wallet.address(), wallet.private_key()

    def get_balance(self, symbol: str) -> Decimal:
        """
        指定された通貨のether単位の残高を取得します。

        Parameters
        ----------
        symbol : str
            通貨種(ETH/ITB)

        Returns
        -------
        Decimal
            指定された通貨の残高
        """

        # ETHの場合
        if symbol == Symbol.ETH:
            balance = self._web3.eth.getBalance(self._address)
            ether_balance: int = self._web3.fromWei(balance, 'ether')
            return Decimal(str(ether_balance))

        # ITBの場合
        elif symbol == Symbol.ITB:
            token_balance = self._contract.functions.balanceOf(self._address).call()
            itb_balance: int = self._web3.fromWei(token_balance, 'ether')
            return Decimal(str(itb_balance))
        return Decimal("0")

    def send_to(self, to_address: str, symbol: str, amount: Decimal) -> tuple:
        """
        指定された通貨を送金します。

        Parameters
        ----------
        to_address : str
            送金先のアドレス
        symbol : str
            送金する通貨種(ETH/ITB)
        amount : Decimal
            送金額(ether単位)

        Returns
        -------
        tuple
            (送金の成否, 発行されたトランザクションID, 失敗理由)
        """
        is_success = False
        error_reason = ""
        tx_hash = ""

        from_address = self._web3.toChecksumAddress(self._address)
        to_address = self._web3.toChecksumAddress(to_address)
        tx_params = {
            'gasPrice': self._web3.toWei('10', 'gwei'),
            'nonce': self._web3.eth.getTransactionCount(from_address),
            'from': from_address,
        }

        # ETHの場合
        if symbol == Symbol.ETH:
            # 残高確認
            eth_balance = self.get_balance(symbol)
            if eth_balance < amount:
                error_reason = ErrorReason.INSUFFICIENT_FUNDS
                return is_success, tx_hash, error_reason

            add_params = {
                'gas': 21000,
                'to': to_address,
                'value': self._web3.toWei(amount, 'ether')
            }
            tx_params.update(add_params)
            try:
                signed_tx = self._web3.eth.account.signTransaction(tx_params, private_key=self._privkey)
                raw_transaction = self._web3.eth.sendRawTransaction(signed_tx.rawTransaction)
                tx_hash = raw_transaction.hex()
                is_success = True
            except Exception as e:
                error_reason = str(e)
        # ITBの場合
        elif symbol == Symbol.ITB:
            # 残高確認
            itb_balance = self.get_balance(symbol)
            if itb_balance < amount:
                error_reason = ErrorReason.INSUFFICIENT_FUNDS
                return is_success, tx_hash, error_reason

            add_params = {'gas': 100000}
            tx_params.update(add_params)
            try:
                transfer_tx = self._contract.functions.transfer(
                    to_address,
                    self._web3.toWei(amount, 'ether'),
                ).buildTransaction(tx_params)
                signed_tx = self._web3.eth.account.signTransaction(transfer_tx, private_key=self._privkey)
                raw_transaction = self._web3.eth.sendRawTransaction(signed_tx.rawTransaction)
                tx_hash = raw_transaction.hex()
                is_success = True
            except Exception as e:
                error_reason = str(e)

        return is_success, tx_hash, error_reason


class ErrorReason:
    INSUFFICIENT_FUNDS = "insufficient funds"


ABI = """
[
    {
        "constant": true,
        "inputs": [],
        "name": "name",
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {
                "name": "spender",
                "type": "address"
            },
            {
                "name": "value",
                "type": "uint256"
            }
        ],
        "name": "approve",
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {
                "name": "sender",
                "type": "address"
            },
            {
                "name": "recipient",
                "type": "address"
            },
            {
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "transferFrom",
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {
                "name": "",
                "type": "uint8"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {
                "name": "spender",
                "type": "address"
            },
            {
                "name": "addedValue",
                "type": "uint256"
            }
        ],
        "name": "increaseAllowance",
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [
            {
                "name": "account",
                "type": "address"
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "symbol",
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {
                "name": "spender",
                "type": "address"
            },
            {
                "name": "subtractedValue",
                "type": "uint256"
            }
        ],
        "name": "decreaseAllowance",
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {
                "name": "recipient",
                "type": "address"
            },
            {
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "transfer",
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [
            {
                "name": "owner",
                "type": "address"
            },
            {
                "name": "spender",
                "type": "address"
            }
        ],
        "name": "allowance",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": false,
        "inputs": [
            {
                "indexed": true,
                "name": "from",
                "type": "address"
            },
            {
                "indexed": true,
                "name": "to",
                "type": "address"
            },
            {
                "indexed": false,
                "name": "value",
                "type": "uint256"
            }
        ],
        "name": "Transfer",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [
            {
                "indexed": true,
                "name": "owner",
                "type": "address"
            },
            {
                "indexed": true,
                "name": "spender",
                "type": "address"
            },
            {
                "indexed": false,
                "name": "value",
                "type": "uint256"
            }
        ],
        "name": "Approval",
        "type": "event"
    }
]
"""
