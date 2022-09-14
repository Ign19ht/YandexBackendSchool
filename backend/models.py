from sqlalchemy import Column, Integer, String, DateTime
from db_manager import DeclarativeBase


# declare models for database


class Items(DeclarativeBase):
    __tablename__ = 'items'
    id = Column(String, primary_key=True, index=True)
    url = Column(String, nullable=True)
    parentId = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    type = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)


class History(DeclarativeBase):
    __tablename__ = 'history'
    id = Column(String, primary_key=True, index=True)
    url = Column(String, nullable=True)
    parentId = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    type = Column(String, nullable=False)
    date = Column(DateTime, primary_key=True, index=True)
