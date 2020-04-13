from flask_sqlalchemy import SQLAlchemy
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
import time

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filters
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure SQLAlchemy Library to use postgresql database
app.secret_key = 'any secret key for cookies but do not show anyone'
app.config['DEBUG'] = True
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:@localhost/myfinance'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import *


@app.route("/", methods=["GET"])
@login_required
def index():
    # stocks_owed = db.execute("SELECT symbol, shares FROM protfolio WHERE id = :id", id=session["user_id"])
    print(session["user_id"])
    stocks_owed = Protfolio.query.filter_by(user_id=session["user_id"]).order_by("symbol")

    net_asset = 0
    total_cost = 0

    hkd = exrate()

    # ------------update protfolio market price and calculate market value-------------
    for stock_owed in stocks_owed:
        # declare variable to use
        symbol = stock_owed.symbol
        shares = stock_owed.shares
        cost = float(stock_owed.shares * stock_owed.avg_price)

        # instant update for each stock
        stock = lookup(symbol)
        while stock is None :
            stock = lookup(symbol)
        print(stock["symbol"],stock["price"])
        time.sleep(1)
        stock_owed.mkt_price = stock["price"]
        mkt_values = shares * stock_owed.mkt_price
        stock_owed.mkt_value = mkt_values
        if stock_owed.symbol[0].isalpha():
            stock_owed.mkt_value_ex = mkt_values * hkd
            total_cost += (cost * hkd)
        else:
            stock_owed.mkt_value_ex = mkt_values
            total_cost += cost
        db.session.commit()
        # db.execute("UPDATE protfolio SET price = :price, mkt_values = :mkt_values WHERE symbol = :symbol and id = :id",\
        # price = price, mkt_values = mkt_values, symbol = symbol, id = session["user_id"] )

        # calculation
        net_asset += stock_owed.mkt_value_ex

    # cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
    # net_asset += cash[0]["cash"]

    updated_protfolio = Protfolio.query.filter_by(user_id=session["user_id"]).order_by("symbol")
    # updated_protfolio = db.execute("SELECT * from protfolio WHERE id=:id GROUP BY symbol", id=session["user_id"])
    print(updated_protfolio)
    return render_template("index.html", stocks=updated_protfolio, net_asset=float(net_asset), total_cost = total_cost)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""

    if request.method == "GET":

        # symbol = request.method.get(symbol)
        return render_template("buy.html")
    else:
        symbol = request.form.get("symbol").upper()
        stock = lookup(symbol)
        stock_name = stock["name"]
        buy_price = float(request.form.get("buy_price"))

        if not stock:
            return flash("Stock does not exist")

        shares = int(request.form.get("shares"))
        if not shares or shares <= 0:
            return flash("Shares must be positive integer only")

        trans_date = request.form.get("trans_date")
        # check cash on hand
        # money = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])

        # if money[0]["cash"] < stock['price'] * shares:
            #return flash("Not enough money")

        # update stock transaction history
        new_transaction = Trans_history(symbol = symbol, user_id=session["user_id"], shares = shares, trans_price = buy_price, trans_date = trans_date)
        db.session.add(new_transaction)
        db.session.commit()
        # db.execute("INSERT INTO history (id, symbol, shares, price) VALUES (:id, :symbol, :shares, :price)", \
                   # id=session["user_id"], symbol=stock["symbol"], shares=shares, price=stock["price"])

        # update user cash
        # db.execute("UPDATE users SET cash = cash - :price WHERE id = :id", \
                   # price=stock["price"] * shares, id=session["user_id"])

        # check user owned stock or not
        stock_owned = Protfolio.query.filter_by(symbol=symbol, user_id=session["user_id"]).first()
        # shares_owned = db.execute("SELECT shares FROM protfolio WHERE id = :id AND symbol = :symbol",
                                  # id=session["user_id"], symbol=stock["symbol"])
        if not stock_owned:
            add_stock = Protfolio(symbol=symbol, user_id=session["user_id"], stock_name=stock_name, shares=shares,
                                  avg_price=buy_price)
            db.session.add(add_stock)
            db.session.commit()
            return redirect(url_for("index"))

            '''db.execute(
                "INSERT INTO protfolio (symbol, stock_name, shares, price, mkt_values, id) VALUES(:symbol, :stock_name, :shares, :price, :mkt_values, :id)", 
                symbol=stock["symbol"], stock_name=stock["name"], shares=shares, price=stock["price"],
                mkt_values=shares * stock["price"], id=session["user_id"])'''

        # add shares to owned stock
        else:
            stock_owned = Protfolio.query.filter_by(symbol=symbol, user_id=session["user_id"]).first()
            '''print(stock_owned.shares)
            print(shares)
            print(stock_owned.avg_price*stock_owned.shares)
            print(shares*buy_price)
            print(stock_owned.shares+shares)'''
            stock_owned.avg_price = round(((stock_owned.avg_price*stock_owned.shares) + (shares*buy_price))/(stock_owned.shares+shares),2)
            stock_owned.shares += shares
            db.session.commit()
            return redirect(url_for("index"))
            # final_shares = shares_owned[0]["shares"] + shares
            # db.execute("UPDATE protfolio SET shares = :shares WHERE symbol = :symbol", shares=final_shares,
                       # symbol=stock["symbol"])

        return redirect(url_for("index"))

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""

    if request.method == "GET":
        return render_template("sell.html")

    else:
        # check for error
        stock = lookup(request.form.get("symbol"))
        symbol = stock["symbol"]
        #stock_name = stock["name"]
        sell_price = float(request.form.get("sell_price"))

        if not stock:
            return flash("Stock does not exist")

        shares = int(request.form.get("shares"))

        if not shares or shares <= 0:
            return flash("Shares must be positive integer only")

        trans_date = request.form.get("trans_date")

        stock_owned = Protfolio.query.filter_by(symbol=symbol, user_id=session["user_id"]).first()
        # shares_owed = db.execute("SELECT shares FROM protfolio WHERE id = :id and symbol = :symbol", \
                                 # id=session["user_id"], symbol=stock["symbol"])

        if not stock_owned:
            return flash("You don't own this stock")
        elif stock_owned.shares < shares:
            return flash("Not enough shares to sell")

        # insert new transaction
        new_transaction = Trans_history(symbol=symbol, user_id=session["user_id"], shares=-shares, trans_price=sell_price,
                                        trans_date=trans_date)
        db.session.add(new_transaction)
        db.session.commit()
        # db.execute("INSERT INTO history (id, symbol, shares, price) VALUES (:id, :symbol, :shares, :price)", \
                   # id=session["user_id"], symbol=stock["symbol"], shares=- shares, price=stock["price"])

        # update user cash
        # db.execute("UPDATE users SET cash = cash + :stock_sold WHERE id = :id", \
                   # id=session["user_id"], stock_sold=stock["price"] * shares)

        # update shares
        # total_shares = shares_owed[0]["shares"] - shares
        total_shares = stock_owned.shares - shares


        if total_shares == 0:
            session.delete(stock_owned)
            db.session.commit()
            #db.execute("DELETE FROM protfolio WHERE id = :id AND symbol = :symbol", id=session["user_id"],
                       #symbol=stock["symbol"])
        else:
            stock_owned.avg_price = round(((stock_owned.avg_price * stock_owned.shares) - (shares * sell_price)) / (
            stock_owned.shares - shares),2)
            stock_owned.shares -= shares
            #db.execute("UPDATE protfolio SET shares = :shares WHERE id = :id AND symbol = :symbol", \
                       #id=session["user_id"], symbol=stock["symbol"], shares=total_shares)

        return redirect(url_for("index"))

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""

    stocks = Trans_history.query.filter_by(user_id=session["user_id"]).order_by(Trans_history.trans_date.desc())
    # stocks = db.execute("SELECT * FROM history WHERE id=:id ORDER BY purchase_date DESC", id=session["user_id"])
    return render_template("history.html", stocks=stocks)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        user_email = request.form.get("email")
        pw = request.form.get("password")

        # ensure username was submitted
        '''if not request.form.get("username"):
            return flash("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return flash("must provide password")'''

        # query database for user
        user = Users.query.filter_by(email=user_email).first()

        # ensure username exists and password is correct
        # if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
        if user is None or not pwd_context.verify(pw, user.password):
            flash("invalid username and/or password")
            return render_template("login.html")

        # remember which user has logged in
        session["user_id"] = user.user_id

        # redirect user to home page
        return redirect(url_for("quote"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "GET":
        return render_template("quote.html")
    elif request.method == "POST":
        quoted = lookup(request.form.get("symbol"))
        if not quoted:
            flash("Symbol not valid")
            return render_template("quote.html")
        else:
            return render_template("quoted.html", quoted=quoted)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    # username = request.form.get("username")
    user_email = request.form.get("email")
    pw = request.form.get("password")
    pw_confirm = request.form.get("password confirm")

    if request.method == "POST":
        # username cannot be blank
        '''if not request.form.get("username"):
            return flash("You must enter the username")'''

        # username duplicated
        check_email = Users.query.filter_by(email=user_email).first()
        if check_email:
            flash("Email has been registered")
            return render_template("register.html")

        # password cannot be blank
        '''if not request.form.get("password"):
            return flash("You must enter password")'''

        # confirm password are the same
        if pw != pw_confirm:
            flash("Please confirm your password")
            return render_template("register.html")

        # hashing pw
        hash = pwd_context.hash(pw)

        # insert username and pw into database
        new_user = Users(email = user_email, password = hash)
        db.session.add(new_user)
        db.session.commit()
        # db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username = request.form.get("username"), hash = hash)

        # find user id
        # user_id = db.execute("SELECT id from users WHERE username = :username", username = request.form.get("username"))

        # login automatically after successfully register
        session["user_id"] = new_user.user_id
        # print (session["users_id"])

        return redirect(url_for("index"))

    else:
        return render_template("register.html")


@app.route("/new", methods=["GET", "POST"])
@login_required
def new():
    return 0


if __name__ == "__main__":
    db.create_all()
    app.run()
