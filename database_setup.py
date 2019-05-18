import sys
from sqlalchemy import Column, String, Numeric, Date, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Stock(Base):
    __tablename__ = 'stock'

    ticker = Column(String(10), primary_key=True)
    dividend = Column(Numeric)
    eps = Column(Numeric)
    price = Column(Numeric)
    last_updated_date = Column(Date, nullable=False)


class StockHistory(Base):
    __tablename__ = 'stock_history'

    ticker = Column(String(10), ForeignKey('stock.ticker'), primary_key=True)
    ds = Column(Date, primary_key=True)
    stock = relationship(Stock)
    price = Column(Numeric) # adjusted close
    last_updated_date = Column(Date, nullable=False)


class Option(Base):
    __tablename__ = 'option'

    ticker = Column(String(10), ForeignKey('stock.ticker'), primary_key=True)
    option_type = Column(String(10), primary_key=True) # call vs put
    expiration_date = Column(Date, primary_key=True)
    strike = Column(Numeric, primary_key=True)
    bid = Column(Numeric)
    ask = Column(Numeric)
    last_updated_date = Column(Date, nullable=False)
    stock = relationship(Stock)


class OptionHistory(Base):
    __tablename__ = 'option_history'

    ds = Column(Date, primary_key=True)
    ticker = Column(String(10), ForeignKey('stock.ticker'), primary_key=True)
    option_type = Column(String(10), primary_key=True) # call vs put
    expiration_date = Column(Date, primary_key=True)
    strike = Column(Numeric, primary_key=True)
    bid = Column(Numeric)
    ask = Column(Numeric)
    last_updated_date = Column(Date, nullable=False)
    stock = relationship(Stock)



engine = create_engine('sqlite:///stockinvestment.db')
Base.metadata.create_all(engine)
