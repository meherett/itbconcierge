import datetime
import threading
import time
from decimal import Decimal

from pytz import timezone
from slackbot.slackclient import SlackClient
from sqlalchemy.sql.functions import func

from slackbot_settings import API_TOKEN, REPORT_CHANNELS

from .model import DBContext, ShopOrder, Symbol, WithdrawalRequest


class ReportPublisher(threading.Thread):
    """
    ITBトークンの利用状況に関するレポートを発行するクラス
    """

    def __init__(self):
        super(ReportPublisher, self).__init__()
        self.setDaemon(False)
        self._db_context = DBContext()
        self._slackclient = SlackClient(API_TOKEN)
        self._should_stop = False
        self._interval = 2000

    def run(self):
        """
        スレッドを開始します。
        """

        self._should_stop = False

        while not self._should_stop:

            start_time = time.time()

            self._db_context.session.expire_all()

            # 現在時刻を取得する
            current_datetime = datetime.datetime.today().astimezone(timezone('Asia/Tokyo'))

            # 平日の場合
            if current_datetime.weekday() in [0, 1, 2, 3, 4]:
                # 朝10時の場合
                if current_datetime.hour == 10:
                    for channel_id in REPORT_CHANNELS:
                        self._slackclient.send_message(
                            channel_id,
                            "昨日のITBトークンの利用状況を報告します。"
                        )
                        # 総幸福量(Gross Happiness)に関するレポートを発行する
                        self.publish_grosshappiness(channel_id, current_datetime-datetime.timedelta(days=1))
                        # ITBカフェの売上高に関するレポートを発行する
                        self.publish_sales(channel_id, current_datetime-datetime.timedelta(days=1))

            past_time = time.time() - start_time
            if past_time < self._interval:
                time.sleep(self._interval - past_time)

    def publish_grosshappiness(self, channel_id: str, designated_date: datetime.datetime):
        """
        総幸福量(Gross Happiness)に関するレポートを発行します。
        """

        date_from = datetime.datetime(*designated_date.timetuple()[:3])
        date_to = date_from + datetime.timedelta(days=1)

        amount = self._db_context.session \
            .query(func.sum(WithdrawalRequest.amount)) \
            .filter(WithdrawalRequest.symbol == Symbol.ITB) \
            .filter(WithdrawalRequest.updated_at >= date_from) \
            .filter(WithdrawalRequest.updated_at < date_to) \
            .all()[0][0]
        if amount is None:
            amount = Decimal("0")

        self._slackclient.send_message(
            channel_id,
            "昨日の総幸福量(Gross Happiness)は「{:.0f} ITB」でした。"
            .format(amount)
        )

    def publish_sales(self, channel_id: str, designated_date: datetime.datetime):
        """
        ITBカフェの売上高に関するレポートを発行します。
        """

        date_from = datetime.datetime(*designated_date.timetuple()[:3])
        date_to = date_from + datetime.timedelta(days=1)

        amount = self._db_context.session \
            .query(func.sum(ShopOrder.price)) \
            .filter(ShopOrder.ordered_at >= date_from) \
            .filter(ShopOrder.ordered_at < date_to) \
            .all()[0][0]
        if amount is None:
            amount = Decimal("0")

        self._slackclient.send_message(
            channel_id,
            "昨日のITBカフェ売上高は「{:.0f} ITB」でした。"
            .format(amount)
        )

    def request_stop(self):
        """
        スレッドの停止をリクエストします。
        """
        self._should_stop = True
