from fastapi import FastAPI, BackgroundTasks
import datetime as dt
from typing import Optional
from pydantic import BaseModel, Field, ValidationError
import mysql.connector as sql
import requests
import random

config = {
    'user': '',
    'password': '',
    'host': '',
    'database': '',
    'raise_on_warnings': True
}

connection = sql.connect(**config)
app = FastAPI()


class TradeDetails(BaseModel):

    buySellIndicator: str = Field(
        description="A value of BUY for buys, SELL for sells.")

    price: float = Field(description="The price of the Trade.")

    quantity: int = Field(description="The amount of units traded.")


class Trade(BaseModel):
    assetclass: Optional[str] = Field(
        alias="assetClass", default="None", description="The asset class of the instrument traded. E.g. Bond, Equity, FX...etc")

    counterparty: Optional[str] = Field(
        default="None", description="The counterparty the trade was executed with. May not always be available")

    instrumentid: str = Field(
        alias="instrumentId", description="The ISIN/ID of the instrument traded. E.g. TSLA, AAPL, AMZN...etc")

    instrumentname: str = Field(
        alias="instrumentName", description="The name of the instrument traded.")

    tradedatetime: dt.datetime = Field(
        alias="tradeDateTime", description="The date-time the Trade was executed")

    buySellIndicator: str = Field(
        description="A value of BUY for buys, SELL for sells.")

    price: float = Field(description="The price of the Trade.")

    quantity: int = Field(description="The amount of units traded.")

    tradeid: str = Field(alias="tradeId", default="None",
                         description="The unique ID of the trade")

    trader: str = Field(description="The name of the Trader")



async def parse(column_names, data):
    tmp = {}
    for column, val in zip(column_names, data):
        tmp[column] = val
    return tmp

db_columns = {"asset_class": "asset_class",
              "counterparty": "counterparty", "instrument_id": "instrument_id", "instrument_name": "instrument_name", "trade_date_time": "trade_date_time", "buySellIndicator": "buySellIndicator", "price": "price", "quantity": "quantity", "trade_id": "trade_id", "trader": "trader"}


@app.get("/")
async def root():
    return {"message": "Please Refer docs to start using api"}


@app.get("/mock_database")
async def mock_db(background_tasks: BackgroundTasks):
    return {"message": "Unauthorized Access"}


@app.get("/get_trade/{id}")
async def get_trade(id: str):
    cursor = connection.cursor()
    query = f"select * from trade where trade_id={id}"
    cursor.execute(query)
    single_row = cursor.fetchone()
    data = {}
    for column, val in zip(cursor.column_names, single_row):
        if column == "trade_date_time":
            val = str(val)
        data[column] = val
    cursor.close()
    if len(data) > 0:
        return {"data": data}
    else:
        return {"data": "Invalid order id"}


@app.get("/get_all_trades/")
async def get_all_trades(page: Optional[int] = 0, sort_by: Optional[str] = None):
    cursor = connection.cursor()

    if sort_by != None and sort_by not in db_columns:
        return {"message": "invalid column name. Please refer to docs for column names"}

    if page > 0 and sort_by:
        query = f"select * from trade order by {sort_by} limit {page},{page+10}"
    elif page > 0:
        query = f"select * from trade limit {page},{page+10}"
    elif sort_by:
        query = f"select * from trade order by {sort_by}"
    else:
        query = "select * from trade"

    cursor.execute(query)
    data = []
    for i in cursor:
        tmp = await parse(cursor.column_names, i)
        data.append(tmp)
    cursor.close()
    if len(data) > 0:
        return data
    return {"data": "You have no trades"}


@app.get("/search_by/")
async def search(search: str, page: Optional[int] = 0, sort_by: Optional[str] = None):
    cursor = connection.cursor()
    if sort_by != None and sort_by not in db_columns:
        return {"message": f"invalid column name. Please refer to docs for column names"}

    if page > 0 and sort_by:
        query = f"select * from trade where counterparty LIKE '{search}%' or instrument_id LIKE '{search}%' or instrument_name LIKE '{search}%' or trader LIKE '{search}%' order by {sort_by} limit {page}, {page+10}"
    elif page > 0:
        query = f"select * from trade where counterparty LIKE '{search}%' or instrument_id LIKE '{search}%' or instrument_name LIKE '{search}%' or trader LIKE '{search}%' limit {page},{page+10}"
    elif sort_by:
        query = f"select * from trade where counterparty LIKE '{search}%' or instrument_id LIKE '{search}%' or instrument_name LIKE '{search}%' or trader LIKE '{search}%' order by {sort_by}"
    else:
        query = f"select * from trade where counterparty LIKE '{search}%' or instrument_id LIKE '{search}%' or instrument_name LIKE '{search}%' or trader LIKE '{search}%'"
    cursor.execute(query)
    data = []
    for i in cursor:
        tmp = await parse(cursor.column_names, i)
        data.append(tmp)
    cursor.close()
    if len(data) > 0:
        return data
    return {"message": "No trades based on defiend parameters"}


@app.get("/filter_trades/")
async def filter_trades(assestClass: Optional[str] = "", end: Optional[dt.date] = dt.date(2023, 1, 1), maxPrice: Optional[float] = 0, minPrice: Optional[float] = 0, start: Optional[dt.date] = dt.date(1999, 1, 1), tradeType: Optional[str] = ""):
    cursor = connection.cursor()
    cursor.execute("select * from trade")
    data = []
    for i in cursor:
        tmp = await parse(cursor.column_names, i)
        data.append(tmp)

    if assestClass:
        data = list(filter(lambda x: x['asset_class'] == assestClass, data))
    if end:
        data = list(filter(lambda x: x['trade_date_time'].date() <= end, data))
    if start:
        data = list(
            filter(lambda x: x['trade_date_time'].date() >= start, data))
    if maxPrice:
        data = list(filter(lambda x: x['price'] <= maxPrice, data))
    if minPrice:
        data = list(filter(lambda x: x['price'] >= minPrice, data))
    if tradeType:
        data = list(filter(lambda x: x['buySellIndicator'] == tradeType, data))
    if len(data) > 0:
        return data
    return {"message": "No trades with defined parameters"}
