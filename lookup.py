import requests as re
import sqlite3
import os


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
-- get_stock_data --

This function calls the IEX api to get real time stock data.

Params:
  symbol [in]   stock symbol for lookup

Returns:
  dictionary with stock name, symbol and latest price
  None on failure
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def get_stock_data(symbol):
    # try and connect to iex api
    try:
        token = os.environ['API_KEY']
        response = re.get("https://cloud.iexapis.com/stable/stock/"
                          "{}/quote?token={}".format(symbol, token))
    except re.exceptions.ConnectionError:
        print("Could not connect to the url")
        return None

    quote = response.json()
    print(quote)
    # get desired info from the response
    try:
        serve = {}
        serve["name"] = quote["companyName"]
        serve["price"] = quote["latestPrice"]
        serve["symbol"] = quote["symbol"]
        return serve
    except KeyError:
        print("unable to find desired information from stock quote")

    # failed to get stock quote
    return None


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
-- get_stock_history --

This function calls the IEX api to get stock history.

Params:
  symbol [in]   stock symbol for lookup

Returns:
  dictionary with stock name, symbol and latest price
  None on failure
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def get_stock_history(symbol):
    try:
        token = os.environ["API_KEY"]
        response = re.get(f"https://cloud.iexapis.com/stable/stock/{symbol}/"
                          f"chart/30d?token={token}&chartCloseOnly=true")
    except re.exceptions.ConnectionError:
        print("failed to connect")
        return None

    json = response.json()

    try:
        history = {}
        history['date'] = [item['date'] for item in json]
        history['close'] = [item['close'] for item in json]
        return history
    except KeyError:
        print("Unable to find desired stock history info")
    
    # failed to get stock history
    return None


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
-- complete_buy_transaction --

This function updates/inserts the requested transaction
in the sqlite3 database.

Params:
  symbol [in]   stock symbol
  shares [in]   number of shares to purchase
  price  [in]   price per share in transaction
  cost   [in]   total cost of order
  user   [in]   current user requesting transaction

Returns:
  No return value 
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def complete_buy_transaction(symbol, shares, price, cost, user):
    # create a table for the specific user if one does not already exist
    with sqlite3.connect("users.db") as db:
        cur = db.cursor()

        # I expect there is a more succinct way to run the below queries
        # i.e INSERT OR UPDATE if symbol is in table
        cur.execute(f"SELECT totalcost, numshares FROM {user} "
                    f"WHERE symbol='{symbol}'")
        fetch = cur.fetchall()
        print(fetch)
        # if symbol is not found in table (first time buying stock)
        if fetch == []:
            cur.execute(f"INSERT INTO {user} VALUES "
                        f"('{symbol}', '{shares}', '{price}', '{cost}', '{0}')")
        else:   
            cur_total = fetch[0][0]
            cur_shares = fetch[0][1]
            total_cost = cur_total + cost # amt paid for shares
            total_shares = shares + cur_shares
            avgper = round(total_cost / total_shares, 2) # avg cost per share
            total_value = round(price * total_shares, 2) # current market value of stocks
            print(total_value)
            print(total_cost)
            return_on_invest = total_value - total_cost
            print(f"cur total: {cur_total}, {cur_shares}")

            cur.execute(f"UPDATE {user} "
                        f"SET numshares='{total_shares}', "
                        f"avgcostper='{avgper}', "
                        f"totalcost='{round(total_cost,2)}', "
                        f"return='{round(return_on_invest,2)}'"
                        f"WHERE symbol='{symbol}'")
        
        for row in cur.execute(f"SELECT * FROM {user}"):
            print(row)
        db.commit()


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
-- complete_sell_transaction --

This function updates the requested transaction
in the sqlite3 database. Function will indicate
failure if there are no available shares to sell.

Params:
  symbol [in]   stock symbol
  shares [in]   number of shares to purchase
  price  [in]   price per share in transaction
  cost   [in]   total cost of order
  user   [in]   current user requesting transaction

Returns:
  0 on Success
  -1 on missing table
  -2 on not enough shares available
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def complete_sell_transaction(symbol, shares, price, cost, user):
    try:
        with sqlite3.connect("users.db") as db:
            cur = db.cursor()

            cur.execute(f"SELECT totalcost, numshares FROM {user} "
                        f"WHERE symbol='{symbol}'")
            fetch = cur.fetchall()

            if fetch == []:
                return -2
            
            cur_total = fetch[0][0]
            cur_shares = fetch[0][1]
            total_cost = cur_total - cost # amt paid for shares
            total_shares = cur_shares - shares
            avgper = round(total_cost / total_shares, 2) # avg cost per share
            total_value = round(price * total_shares, 2) # current market value of stocks
            return_on_invest = total_value - total_cost
            print(f"cur total: {cur_total}, {cur_shares}")

            if total_shares < 0:
                return -2

            cur.execute(f"UPDATE {user} "
                        f"SET numshares='{total_shares}', "
                        f"avgcostper='{avgper}', "
                        f"totalcost='{round(total_cost,2)}', "
                        f"return='{round(return_on_invest,2)}'"
                        f"WHERE symbol='{symbol}'")
            
            for row in cur.execute(f"SELECT * FROM {user}"):
                print(row) 
            db.commit()
        return 0
    except sqlite3.OperationalError:
        # table is not found which means no buy orders have been fulfilled
        return -1


if __name__ == "__main__":
    get_stock_history("NFLX")