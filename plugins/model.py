from sqlalchemy import (TIMESTAMP, Column, Index, Integer, Numeric, Text,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    userid = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    privkey = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)

    __table_args__ = (
        Index("ui_users_01", userid, unique=True),
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
