from __future__ import annotations

from sqlalchemy import (TIMESTAMP, Boolean, Column, Index, Integer, Numeric,
                        Text, create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class DBContext:

    def __init__(self, connection_str: str = "sqlite:///itb_concierge.sqlite"):
        engine = create_engine(connection_str, echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self._session = Session()

    @property
    def session(self):
        return self._session


class User(Base):
    __tablename__ = 'user'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    slack_uid = Column(Text, nullable=False)
    slack_name = Column(Text, nullable=False)
    eth_address = Column(Text, nullable=True)
    eth_privkey = Column(Text, nullable=True)
    notification_enabled = Column(Boolean, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)

    __table_args__ = (
        Index("ui_user_01", slack_uid, unique=True),
        Index("ui_user_02", eth_address, unique=True),
    )

    @staticmethod
    def get_user_from_slack_uid(db_context: DBContext, slack_uid: str) -> User:
        """
        ユーザー情報を取得します。

        Parameters
        ----------
        db_context:
            DBセッション
        slack_uid: str
            SlackのユーザーID

        Returns
        -------
        User
            ユーザー情報
        """

        # ユーザーを照会する
        user = db_context.session.query(User) \
            .filter(User.slack_uid == slack_uid) \
            .first()

        return user

    @staticmethod
    def get_user_from_eth_address(db_context: DBContext, eth_address: str) -> User:
        """
        ユーザー情報を取得します。

        Parameters
        ----------
        db_context:
            DBセッション
        eth_address: str
            ETHのアドレス

        Returns
        -------
        User
            ユーザー情報
        """

        # ユーザーを照会する
        user = db_context.session.query(User) \
            .filter(User.eth_address == eth_address) \
            .first()

        return user


class WithdrawalRequest(Base):
    __tablename__ = 'withdrawal_request'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    symbol = Column(Text, nullable=False)
    amount = Column(Numeric, nullable=False)
    from_address = Column(Text, nullable=False)
    to_address = Column(Text, nullable=False)
    purpose = Column(Text, nullable=False)
    is_success = Column(Boolean, nullable=True)
    error_reason = Column(Text, nullable=True)
    tx_hash = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)

    __table_args__ = (
        Index("ui_withdrawal_request_01", tx_hash, unique=False),
    )


class ShopItem(Base):
    __tablename__ = 'shop_item'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    price = Column(Numeric, nullable=False)
    available = Column(Boolean, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class ShopOrder(Base):
    __tablename__ = 'shop_order'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    userid = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    price = Column(Numeric, nullable=False)
    ordered_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class Symbol:

    ETH = "ETH"
    ITB = "ITB"
