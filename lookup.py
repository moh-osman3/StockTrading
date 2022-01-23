import requests as re
import sqlite3
import os
from flask import render_template

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


def complete_buy_transaction(symbol, shares, price, cost, user):
    # create a table for the specific user if one does not already exist
    with sqlite3.connect("users.db") as db:
        cur = db.cursor()

        cur.execute(f"CREATE TABLE if not exists {user} ("
                     "symbol VARCHAR(255) PRIMARY KEY,"
                     "numshares INT,"
                     "avgcostper FLOAT,"
                     "totalcost FLOAT,"
                     "return FLOAT)")

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


def complete_sell_transaction(symbol, shares, price, cost, user):
    try:
        with sqlite3.connect("users.db") as db:
            cur = db.cursor()

            cur.execute(f"SELECT totalcost, numshares FROM {user} "
                        f"WHERE symbol='{symbol}'")
            fetch = cur.fetchall()

            if fetch == []:
                return -1
            
            cur_total = fetch[0][0]
            cur_shares = fetch[0][1]
            total_cost = cur_total - cost # amt paid for shares
            total_shares = cur_shares - shares
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
        return 0
    except sqlite3.OperationalError:
        return -1
        return render_template("error.html", error="You must buy stocks before trying to sell!")
     

if __name__ == "__main__":
    get_stock_data("NFLX")