import threading
import time
from decimal import Decimal

from slackbot.slackclient import SlackClient
from sqlalchemy import asc, desc
from sqlalchemy.sql.functions import func

from slackbot_settings import (API_TOKEN, ITB_FOUNDATION_ADDRESS,
                               ITB_FOUNDATION_PRIVKEY)

from .model import DBContext, Symbol, User, WithdrawalRequest
from .wallet import WalletController


class WithdrawalController:
    """
    送金依頼を受け付けるクラス
    """

    def __init__(self, db_context: DBContext):
        self._db_context = db_context

    def request_to_withdraw(
        self,
        symbol: str,
        amount: Decimal,
        from_address: str,
        to_address: str,
        purpose: str
    ) -> int:
        """
        送金依頼を登録します。

        Parameters
        ----------
        symbol : str
            送金する通貨種(ETH/ITB)
        amount : Decimal
            送金額
        from_address : str
            送金元のアドレス
        to_address : str
            送金先のアドレス
        purpose : str
            送金目的

        Returns
        -------
        int
            送金依頼ID
        """

        wh = WithdrawalRequest(
            symbol=symbol,
            amount=amount,
            from_address=from_address,
            to_address=to_address,
            purpose=purpose,
            created_at=func.now(),
            updated_at=func.now()
        )
        self._db_context.session.add(wh)
        self._db_context.session.flush()

        return wh.id

    def get_request_progress(self, request_id: int) -> str:
        """
        送金依頼の進捗を取得します。

        Parameters
        ----------
        request_id : int
            送金依頼ID

        Returns
        -------
        str
            送金依頼の進捗
        """

        wr = self._db_context.session.query(WithdrawalRequest) \
            .filter(WithdrawalRequest.id == request_id) \
            .first()

        if wr is None:
            return "Not Found"
        elif wr.is_success is None:
            return "Pending"
        elif wr.is_success == True:
            return "Success"
        elif wr.is_success == False:
            return wr.error_reason
        else:
            return "Unknown Error"


class WithdrawalExecutor(threading.Thread):
    """
    送金依頼を監視し、送金するクラス
    """

    def __init__(self):
        super(WithdrawalExecutor, self).__init__()
        self.setDaemon(False)
        self._db_context = DBContext()
        self._should_stop = False
        self._withdrawal_interval = 60
        self._slackclient = SlackClient(API_TOKEN)

    def run(self):
        """
        スレッドを開始します。
        """

        self._should_stop = False

        while not self._should_stop:

            start_time = time.time()

            self._db_context.session.expire_all()

            is_resend = False

            # 送金依頼を取得する
            wreq = self._db_context.session.query(WithdrawalRequest) \
                .filter(WithdrawalRequest.is_success.is_(None)) \
                .order_by(asc(WithdrawalRequest.id)) \
                .first()

            # 未着手の送金依頼がないとき、エラーとなった送金依頼を再送する
            if wreq is None:
                is_resend = True
                wreq = self._db_context.session.query(WithdrawalRequest) \
                    .filter(WithdrawalRequest.is_success == False) \
                    .order_by(asc(WithdrawalRequest.id)) \
                    .first()

            if wreq:

                # 送金元ユーザーを取得する
                if wreq.from_address == ITB_FOUNDATION_ADDRESS:
                    from_user = None
                    from_address = ITB_FOUNDATION_ADDRESS
                    from_privkey = ITB_FOUNDATION_PRIVKEY
                else:
                    from_user = User.get_user_from_eth_address(self._db_context, wreq.from_address)
                    from_address = from_user.eth_address
                    from_privkey = from_user.eth_privkey

                # 送金先ユーザーを取得する
                to_user = User.get_user_from_eth_address(self._db_context, wreq.to_address)

                # 送金元・送金先が同一の依頼を取得する
                amount_grp = Decimal("0")
                wreq_grp = []
                if not is_resend:
                    wreq_grp = self._db_context.session.query(WithdrawalRequest) \
                        .filter(WithdrawalRequest.is_success.is_(None)) \
                        .filter(WithdrawalRequest.from_address == wreq.from_address) \
                        .filter(WithdrawalRequest.to_address == wreq.to_address) \
                        .filter(WithdrawalRequest.purpose == wreq.purpose) \
                        .filter(WithdrawalRequest.id != wreq.id) \
                        .order_by(asc(WithdrawalRequest.id)) \
                        .all()

                    amount_grp = sum(map(lambda x: x.amount, wreq_grp))

                # 送金する
                wc = WalletController(from_address, from_privkey)
                is_success, tx_hash, error_reason = wc.send_to(wreq.to_address, wreq.symbol, wreq.amount + amount_grp)

                # 送金結果を反映する
                wreq.is_success = is_success
                wreq.tx_hash = tx_hash
                wreq.error_reason = error_reason
                wreq.updated_at = func.now()
                for item in wreq_grp:
                    item.is_success = is_success
                    item.tx_hash = tx_hash
                    item.error_reason = error_reason
                    item.updated_at = func.now()
                self._db_context.session.commit()

                # 送金結果を通知する
                if wreq.purpose == "ガス代補充":
                    pass
                elif wreq.purpose == "新規登録ボーナス":

                    # 送金先ユーザーに通知する
                    channel_id = self._slackclient.open_dm_channel(to_user.slack_uid)
                    if wreq.is_success == True:
                        self._slackclient.send_message(
                            channel_id,
                            "新規登録ボーナスを獲得しました:laughing: (+{:.0f} ITB)"
                            .format(wreq.amount)
                        )
                    else:
                        self._slackclient.send_message(
                            channel_id,
                            "新規登録ボーナスの獲得に失敗しました:sob:"
                        )

                elif wreq.purpose == "いいね！チップ":

                    # 送金先ユーザーに通知する
                    channel_id = self._slackclient.open_dm_channel(to_user.slack_uid)
                    if wreq.is_success == True:
                        self._slackclient.send_message(
                            channel_id,
                            "いいね！チップを獲得しました:laughing: (+{:.0f} ITB)"
                            .format(wreq.amount)
                        )

                    # 送金元ユーザーに通知する
                    channel_id = self._slackclient.open_dm_channel(from_user.slack_uid)
                    if wreq.is_success == True:
                        self._slackclient.send_message(
                            channel_id,
                            "いいね！チップを送信しました:laughing: (-{:.0f} ITB)"
                            .format(wreq.amount)
                        )
                    else:
                        self._slackclient.send_message(
                            channel_id,
                            "いいね！チップの送信に失敗しました:sob:"
                        )

                elif wreq.purpose == "グッドコミュニケーションボーナス":

                    # 送金先ユーザーに通知する
                    channel_id = self._slackclient.open_dm_channel(to_user.slack_uid)
                    if wreq.is_success == True:
                        self._slackclient.send_message(
                            channel_id,
                            "グッドコミュニケーションボーナスを獲得しました:laughing: (+{:.0f} ITB)"
                            .format(wreq.amount)
                        )

            past_time = time.time() - start_time
            if past_time < self._withdrawal_interval:
                time.sleep(self._withdrawal_interval - past_time)

    def request_stop(self):
        """
        スレッドの停止をリクエストします。
        """
        self._should_stop = True
