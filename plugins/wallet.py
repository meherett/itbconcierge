from decimal import Decimal
from .model import Symbol


class Wallet(object):

    def __init__(self, address: str, privkey: str):
        self._address = address
        self._privkey = privkey

    @staticmethod
    def create_address() -> tuple:
        """
        新規アドレスを発行します。

        Returns
        -------
        tuple
            新規発行したアドレスと秘密鍵を返す。
            (new_address, new_privkey)
        """
        adderss = "new_address"
        privkey = "new_privkey"
        return adderss, privkey

    def get_balance(self, symbol: str) -> Decimal:
        """
        指定された通貨の残高を取得します。

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
            return Decimal("1")

        # ITBの場合
        elif symbol == Symbol.ITB:
            return Decimal("1000")

    def sendto(self, address: str, symbol: str, amount: Decimal) -> tuple:
        """
        指定された通貨を送金します。

        Parameters
        ----------
        address : str
            送金先のアドレス
        symbol : str
            送金する通貨種(ETH/ITB)
        amount : Decimal
            送金額

        Returns
        -------
        turple
            (送金の成否, 発行されたトランザクションID, 失敗理由)
        """

        # ETHの場合
        if symbol == Symbol.ETH:
            is_success = True
            tx_id = "transaction id"
            error_reason = ""

        # ITBの場合
        elif symbol == Symbol.ITB:
            is_success = True
            tx_id = "transaction id"
            error_reason = ""

        return is_success, tx_id, error_reason
