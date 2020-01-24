from sqlalchemy import (TIMESTAMP, Column, Index, Integer, Numeric, Text,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    slack_uid = Column(Text, nullable=False)
    eth_address = Column(Text, nullable=True)
    eth_privkey = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)

    __table_args__ = (
        Index("ui_user_01", slack_uid, unique=True),
    )


class Symbol:

    ETH = "ETH"
    ITB = "ITB"


class DBContext:

    def __init__(self, connection_str: str = "sqlite:///itb_concierge.sqlite"):
        engine = create_engine(connection_str, echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self._session = Session()

    @property
    def session(self):
        return self._session
