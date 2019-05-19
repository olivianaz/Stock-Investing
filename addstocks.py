from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database_setup import Stock, StockHistory, Base, Option, OptionHistory
from datetime import date, datetime
from sqlalchemy.exc import *
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
import json
import time

from bs4 import BeautifulSoup
from web_util import *
import re
import pandas as pd
import numpy as np

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
        print('Getting historical prices for {}'.format(ticker))
        url = url_template.format(ticker, apikey)
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


def getOptionData(ticker):
    base_url = "https://www.nasdaq.com/symbol/{}/option-chain".format(ticker)
    url = base_url + "?expir=week&dateindex=-1" #"?expir=stan&dateindex=-1"
    page_content = simple_get(url)
    html = BeautifulSoup(page_content, 'html.parser')

    chart_div = html.find("div", class_="OptionsChain-chart")
    chart_headers = []
    for th in chart_div.find_all("th"):
        if th.find("a"):
            chart_headers.append(re.search(r'\".+\"', th.find("a").text)[0].replace('\"', ''))
        else:
            chart_headers.append(th.text)
    ## update for duplicate column names
    seen = []
    for c, col in enumerate(chart_headers):
        if col == 'Root':
            chart_headers[c] = 'Ticker'
        if col in seen:
            chart_headers[c] = col + "_2"
        else:
            seen.append(col)

    rows = chart_div.findAll("tr")
    rowlist = []
    for i, row in enumerate(rows):
        ## Find rows that have option price data
        ## These rows would have 2 <td>s with links to the option price details for the corresponding call/put, expiry and strike
        results = row.find_all(href=re.compile("option-chain"))

        if len(results) > 0:
            #expiry_date = datetime.strptime(results[0].text, '%b %d, %Y')
            rowlist.append([td.text for td in row.find_all("td")])
    df = pd.DataFrame(rowlist)

    if df.shape[0] > 0:
        df.columns = chart_headers
    return df

def batchAddOption(session, full_ticker_list):
    # only get data for tickers that have not been updated today
    q = (session.query(Option.ticker, func.max(Option.last_updated_date))
                .filter(Option.ticker.in_(full_ticker_list))
                .group_by(Option.ticker)
                .having(func.max(Option.last_updated_date)==date.today())
        )

    tickers_updated_today = [result[0] for result in q.all()]
    ticker_list = [ticker for ticker in full_ticker_list if ticker not in tickers_updated_today]


    option_list = []
    call_columns = ['Ticker', 'Calls','Strike','Bid', 'Ask', 'Volume']
    put_columns = ['Ticker', 'Put','Strike','Bid_2', 'Ask_2', 'Volume_2']

    for ticker in ticker_list:
        df = getOptionData(ticker)
        if df.shape[0] > 0:
            # convert expiration date to date time datatype
            df['Calls'] = pd.to_datetime(df['Calls'])
            df['Put'] = pd.to_datetime(df['Put'])
            call_df = df[df['Bid'] != ''][call_columns]
            call_df['OptionType'] = 'call'
            put_df = df[df['Bid_2'] != ''][put_columns]
            put_df['OptionType'] = 'put'

            call_df.rename(columns={'Calls':'Expiration'}, inplace=True)
            put_df.rename(columns={'Put':'Expiration', 'Bid_2': 'Bid', 'Ask_2': 'Ask', 'Volume_2': 'Volume'},
                                   inplace=True)
            option_list.extend(call_df.values.tolist())
            option_list.extend(put_df.values.tolist())
        time.sleep(5)

    cnt = 0
    for rec in option_list:
        option = Option(ticker=rec[0],
                        expiration_date=rec[1],
                        strike=rec[2],
                        bid=rec[3],
                        ask=rec[4],
                        volume=rec[5],
                        option_type=rec[6],
                        last_updated_date=date.today()
                        )

        try:
            session.add(option)
            session.commit()
            cnt += 1
        except IntegrityError as ex:
            session.rollback()
            print(ex.args, "ticker: ", option.ticker, option.expiration_date, option.strike, option.option_type)

    print("added {} option data to stockinvestment.db".format(cnt))


if __name__ == '__main__':
    # add stocks to db
    ticker_list = ['LYFT', 'FB', 'XLNX', 'WFC', 'ABBV', 'SYF', 'SRG']
    session = startSession('sqlite:///stockinvestment.db')
    batchAddStock(session, ticker_list)

    # add historical data
    batchAddStockHistory(session, ticker_list)

    # add options data
    batchAddOption(session, ticker_list)
