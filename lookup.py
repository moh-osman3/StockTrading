import requests as re
import os

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

if __name__ == "__main__":
    get_stock_data("NFLX")