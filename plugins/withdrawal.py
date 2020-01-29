import datetime
import threading
import time
from decimal import Decimal

from pytz import timezone
from slackbot.slackclient import SlackClient
from sqlalchemy import asc, desc, distinct
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

        request = WithdrawalRequest(
            symbol=symbol,
            amount=amount,
            from_address=from_address,
            to_address=to_address,
            purpose=purpose,
            created_at=func.now(),
            updated_at=func.now()
        )
        self._db_context.session.add(request)
        self._db_context.session.flush()

        return request.id

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

        request = self._db_context.session.query(WithdrawalRequest) \
            .filter(WithdrawalRequest.id == request_id) \
            .first()

        if request is None:
            return "Not Found"
        elif request.is_success is None:
            return "Pending"
        elif request.is_success == True:
            return "Success"
        elif request.is_success == False:
            return request.error_reason
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
        self._slackclient = SlackClient(API_TOKEN)
        self._should_stop = False
        self._withdrawal_interval = 1

    def run(self):
        """
        スレッドを開始します。
        """

        self._should_stop = False

        while not self._should_stop:

            start_time = time.time()

            self._db_context.session.expire_all()

            # 休息中の送金元リスト
            updated_from = (datetime.datetime.now() - datetime.timedelta(seconds=60)).astimezone(timezone('UTC'))
            rest_address = self._db_context.session \
                .query(distinct(WithdrawalRequest.from_address)) \
                .filter(WithdrawalRequest.updated_at >= updated_from) \
                .all()
            rest_address = list(map(lambda x: x[0], rest_address))

            # 未着手の送金依頼を取得する
            prompt = self._db_context.session.query(WithdrawalRequest) \
                .filter(WithdrawalRequest.is_success.is_(None)) \
                .filter(WithdrawalRequest.from_address.notin_(rest_address)) \
                .order_by(asc(WithdrawalRequest.symbol), asc(WithdrawalRequest.id)) \
                .first()

            # 未着手の送金依頼を取得できた場合
            if prompt:
                # 送金元・送金先・送金目的が同一の依頼を再取得する
                requests = self._db_context.session.query(WithdrawalRequest) \
                    .filter(WithdrawalRequest.is_success.is_(None)) \
                    .filter(WithdrawalRequest.from_address == prompt.from_address) \
                    .filter(WithdrawalRequest.to_address == prompt.to_address) \
                    .filter(WithdrawalRequest.purpose == prompt.purpose) \
                    .order_by(asc(WithdrawalRequest.id)) \
                    .all()
            # 未着手の送金依頼を取得できない場合
            else:
                # エラーとなった送金依頼を取得する
                prompt = self._db_context.session.query(WithdrawalRequest) \
                    .filter(WithdrawalRequest.is_success == False) \
                    .order_by(asc(WithdrawalRequest.id)) \
                    .first()
                if prompt:
                    requests = [prompt]
                else:
                    requests = []

            if len(requests) > 0:

                # 送金元ユーザーを取得する
                if requests[0].from_address == ITB_FOUNDATION_ADDRESS:
                    from_user = None
                    from_address = ITB_FOUNDATION_ADDRESS
                    from_privkey = ITB_FOUNDATION_PRIVKEY
                else:
                    from_user = User.get_user_from_eth_address(self._db_context, requests[0].from_address)
                    from_address = from_user.eth_address
                    from_privkey = from_user.eth_privkey

                # 送金先ユーザーを取得する
                to_user = User.get_user_from_eth_address(self._db_context, requests[0].to_address)

                # 送金額を集計する
                total_amount = sum(map(lambda x: x.amount, requests))

                # 送金する
                wc = WalletController(from_address, from_privkey)
                is_success, tx_hash, error_reason = wc.send_to(requests[0].to_address, requests[0].symbol, total_amount)

                # 送金結果を反映する
                for request in requests:
                    request.is_success = is_success
                    request.tx_hash = tx_hash
                    request.error_reason = error_reason
                    request.updated_at = func.now()
                self._db_context.session.commit()

                # 送金結果を通知する
                if requests[0].purpose == "ガス代補充":
                    pass

                elif requests[0].purpose == "新規登録ボーナス":

                    # 送金先ユーザーに通知する
                    if to_user.notification_enabled:
                        channel_id = self._slackclient.open_dm_channel(to_user.slack_uid)
                        if requests[0].is_success == True:
                            self._slackclient.send_message(
                                channel_id,
                                str(
                                    "新規登録ボーナスを獲得しました:laughing: (+{:.0f} ITB)\n" +
                                    "https://ropsten.etherscan.io/tx/{}"
                                ).format(total_amount, requests[0].tx_hash)
                            )
                        else:
                            self._slackclient.send_message(
                                channel_id,
                                str(
                                    "新規登録ボーナスの獲得に失敗しました:sob:\n" +
                                    "{}"
                                ).format(requests[0].error_reason)
                            )

                elif requests[0].purpose == "いいね！チップ":

                    # 送金先ユーザーに通知する
                    if to_user.notification_enabled:
                        channel_id = self._slackclient.open_dm_channel(to_user.slack_uid)
                        if requests[0].is_success == True:
                            self._slackclient.send_message(
                                channel_id,
                                str(
                                    "いいね！チップを獲得しました:laughing: (+{:.0f} ITB)\n" +
                                    "https://ropsten.etherscan.io/tx/{}"
                                ).format(total_amount, requests[0].tx_hash)
                            )

                    # 送金元ユーザーに通知する
                    if from_user.notification_enabled:
                        channel_id = self._slackclient.open_dm_channel(from_user.slack_uid)
                        if requests[0].is_success == True:
                            self._slackclient.send_message(
                                channel_id,
                                str(
                                    "いいね！チップを送信しました:laughing: (-{:.0f} ITB)\n" +
                                    "https://ropsten.etherscan.io/tx/{}"
                                ).format(total_amount, requests[0].tx_hash)
                            )
                        else:
                            self._slackclient.send_message(
                                channel_id,
                                str(
                                    "いいね！チップの送信に失敗しました:sob:\n" +
                                    "{}"
                                ).format(requests[0].error_reason)
                            )

                elif requests[0].purpose == "グッドコミュニケーションボーナス":

                    # 送金先ユーザーに通知する
                    if to_user.notification_enabled:
                        channel_id = self._slackclient.open_dm_channel(to_user.slack_uid)
                        if requests[0].is_success == True:
                            self._slackclient.send_message(
                                channel_id,
                                str(
                                    "グッドコミュニケーションボーナスを獲得しました:laughing: (+{:.0f} ITB)\n" +
                                    "https://ropsten.etherscan.io/tx/{}"
                                ).format(total_amount, requests[0].tx_hash)
                            )

            past_time = time.time() - start_time
            if past_time < self._withdrawal_interval:
                time.sleep(self._withdrawal_interval - past_time)

    def request_stop(self):
        """
        スレッドの停止をリクエストします。
        """
        self._should_stop = True
