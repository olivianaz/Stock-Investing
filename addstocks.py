from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database_setup import Stock, StockHistory, Base
from datetime import date, datetime
from sqlalchemy.exc import *
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
import json
import time

def startSession(db):
    engine = create_engine(db)
    # Bind the engine to the metadata of the Base class so that the
    # declaratives can be accessed through a DBSession instance
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    # A DBSession() instance establishes all conversations with the database
    # and represents a "staging zone" for all the objects loaded into the
    # database session object. Any change made against the objects in the
    # session won't be persisted into the database until you call
    # session.commit(). If you're not happy about the changes, you can
    # revert all of them back to the last commit by calling
    # session.rollback()
    session = DBSession()
    return session

def batchAddStock(session, stock_list):
    # Add various public stocks
    cnt = 0

    for ticker in stock_list:
        try:
            session.add(Stock(ticker=ticker, last_updated_date=date.today()))
            session.commit()
            cnt += 1
        except IntegrityError as ex:
            session.rollback()
            print(ex.args, "ticker: ", ticker)

    print("added {} stocks to stockinvestment.db".format(cnt))

def batchAddStockHistory(session, full_ticker_list):
    # only get data for tickers that have not been updated today
    q = (session.query(StockHistory.ticker, func.max(StockHistory.last_updated_date))
                .filter(StockHistory.ticker.in_(full_ticker_list))
                .group_by(StockHistory.ticker)
                .having(func.max(StockHistory.last_updated_date)==date.today())
        )

    tickers_updated_today = [result[0] for result in q.all()]

    ticker_list = [ticker for ticker in full_ticker_list if ticker not in tickers_updated_today]
    json_dict = {}

    with open('apikey.txt', 'r') as f:
        apikey = f.read().strip()

    url_template = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={}&apikey={}'
    for ticker in ticker_list:
        print('Getting historical prices for {}'.format(ticker, apikey))
        url = url_template.format(ticker)
        resp = get(url)
        content = json.loads(resp.content)
        json_dict[ticker] = content
        time.sleep(15)
    stock_history_list = []
    for ticker in json_dict:
        time_series = json_dict[ticker]['Time Series (Daily)']
        for ds in time_series:
            price = time_series[ds]['5. adjusted close']
            stock_history = StockHistory(ticker=ticker,
                                         ds=datetime.strptime(ds, "%Y-%m-%d").date(),
                                         price=price,
                                         last_updated_date = date.today())
            stock_history_list.append(stock_history)
    cnt = 0
    for stock_history in stock_history_list:
        try:
            session.add(stock_history)
            session.commit()
            cnt += 1
        except IntegrityError as ex:
            session.rollback()
            print(ex.args, "ticker: ", stock_history.ticker, "ds: ", stock_history.ds)
    print("added {} historical stock prices to stockinvestment.db".format(cnt))


if __name__ == '__main__':
    # add stocks to db
    ticker_list = ['LYFT', 'FB', 'XLNX', 'WFC', 'ABBV', 'SYF', 'SRG']
    session = startSession('sqlite:///stockinvestment.db')
    batchAddStock(session, ticker_list)

    # add historical data
    batchAddStockHistory(session, ticker_list)
