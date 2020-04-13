import csv
import urllib.request
import json
import math

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Renders message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# transform symbol to hong kong stock
def stock_market(symbol):
    symbol = str(symbol)
    if symbol[0].isdigit():
        while len(symbol) < 4:
            symbol = '0' + symbol
        symbol = symbol + '.HK'
        return symbol
    else:
        return symbol

def lookup(symbol):
    """Look up quote for symbol."""

    # reject symbol if it starts with caret
    if symbol.startswith("^"):
        return None

    # reject symbol if it contains comma
    if "," in symbol:
        return None

    # transform symbol to hong kong stock
    symbol = stock_market(symbol)
    # print(symbol)

    # query Alpha Vantage for quote instead
    # https://www.alphavantage.co/documentation/
    try:
        # GET CSV
        url = f"https://www.alphavantage.co/query?apikey=E9S99QEWWD4NU5DG&datatype=csv&function=TIME_SERIES_DAILY&interval=1min&symbol={symbol}"
        webpage = urllib.request.urlopen(url)

        # parse CSV
        datareader = csv.reader(webpage.read().decode("utf-8").splitlines())

        # ignore first row
        next(datareader)

        # parse second row
        row = next(datareader)

        # ensure stock exists
        try:
            price = float(row[4])
        except:
            return None

        # return stock's name (as a str), price (as a float), and (uppercased) symbol (as a str)
        return {
            "name": symbol.upper(), # for backward compatibility with Yahoo
            "price": price,
            "symbol": symbol.upper()
        }

    except:
        return None

def exrate():
    """Look up HK currency exchange rate."""

    # query Alpha Vantage for quote instead
    # https://www.alphavantage.co/documentation/
    try:
        # GET CSV
        url = "https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=HKD&apikey=E9S99QEWWD4NU5DG"
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())

        print(round(float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]), 2))
        # return stock's name (as a str), price (as a float), and (uppercased) symbol (as a str)
        return round(float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]), 2)

    except:
        return None


def usd(value):
    """Formats value as USD."""
    return f"${value:,.2f}"
