# import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd, is_positive_int

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    user_id = session['user_id']
    users = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    username = users[0]['username']
    cash = users[0]['cash']

    #Get current assets
    assets = db.execute("SELECT * FROM assets WHERE user_id = ?", user_id)

    #Add current price and total asset data into the assets list
    assets_num = len(assets)
    invests_balance = 0
    for i in range(assets_num):
        symbol = assets[i]["symbol"]
        shares = assets[i]["shares"]

        #get stock data
        stock = lookup(symbol)

        #get current price of the stock
        price = stock["price"]
        assets[i]["price"] = usd(price)

        #calcurate the market value of the stock
        market_value = shares * price
        assets[i]["market_value"] = usd(market_value)

        #calcurate the total balance
        invests_balance += market_value

        #get the name of the stock
        stockname = stock["name"]
        assets[i]["name"] = stockname

    #Get the date time of get market price
    now = datetime.now()
    now_str = now.strftime("%B %d, %y %H:%M")

    # Calculate total balance
    total_balance = invests_balance + cash

    return render_template("index.html", username=username, cash=usd(cash), assets=assets, assets_num=assets_num, total_balance=usd(total_balance), invests_balance=usd(invests_balance), now=now_str)

    # return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        # Ensure symbol was submitted
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("must provide symbol", 400)

        # Ensure shares was submitted
        shares = request.form.get("shares")
        if not shares:
            return apology("must provide shares", 400)

        # Ensure shares was integer
        if is_positive_int(shares) == False:
            return apology("must provide positive integer for shares", 400)
        shares = int(shares)

        # Get the quote of the symbol
        quote = lookup(symbol)

        #Ensure the symbol is valid
        if quote == None:
            return apology("invalid symbol", 400)

        price = quote["price"]

        buy = True
        user_id = session['user_id']

        # Grt the balance of the user
        balance = db.execute("SELECT cash FROM users WHERE id = ?", user_id)

        # Ensure the balance is enough
        cash = balance[0]["cash"]
        deal_price = price * shares
        if cash < deal_price:
            return apology("Not enough balance", 400)
        current_cash = cash - deal_price

        #Insert transaction data to transactions table
        db.execute("INSERT INTO transactions (symbol, price, shares, buy, user_id) VALUES (?, ?, ?, ?, ?)", symbol, price, shares, buy, user_id)

        #Update the latest chsh after the transaction
        db.execute("UPDATE users SET cash = ? WHERE id = ?", current_cash, user_id)

        #Insert new asset data
        rows = db.execute("SELECT * FROM assets WHERE user_id = ? AND symbol = ?", user_id, symbol)
        if len(rows) == 0:
            db.execute("INSERT INTO assets (symbol, shares, user_id) VALUES (?, ?, ?)", symbol, shares, user_id)
        else:
            pre_shares = rows[0]["shares"]
            latest_shares = pre_shares + shares
            db.execute("UPDATE assets SET shares = ? WHERE user_id = ? AND symbol = ?", latest_shares, user_id, symbol)

        #Redirest to toppage
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    """Add deposit"""
    #Get current chash balance
    user_id = session['user_id']
    current_cash_list = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    current_cash = current_cash_list[0]['cash']

    if request.method == "POST":

        # Ensure amount of cash was submitted
        cash_str = request.form.get("cash")
        if not cash_str:
            return apology("must provide amount of cash", 403)

        cash = float(cash_str)

        if cash <= 0:
            return apology("must provide positive number", 403)

        #Insert new deposit transaction on cash table
        deposit = True
        db.execute("INSERT INTO cash (amount, deposit, user_id) VALUES (?, ?, ?)", cash, deposit, user_id)

        #Update the latest cash on users table
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + current_cash, user_id)

        #Redirest to toppage
        return redirect("/")
    else:
        username_list = db.execute("SELECT username FROM users WHERE id = ?", user_id)
        username = username_list[0]['username']
        return render_template("cash.html", username=username, current_cash=current_cash)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session['user_id']

    #Get transaction history of the user
    historys = db.execute("SELECT * FROM transactions WHERE user_id = ?", user_id)
    history_num = len(historys)

    return render_template("history.html", historys=historys, history_num=history_num)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        username = request.form.get("username")
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        password = request.form.get("password")
        if not password:
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        stored_hash = rows[0]["hash"]

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(stored_hash, password):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/quoted")
@login_required
def quoted():
    """Show price of stocks"""
    return render_template("quoted.html")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":

        # Ensure symbol was submitted
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("must provide symbol", 400)

        # Get quote of the symbol
        quote = lookup(symbol)

        #Ensure symbol was valid
        if quote == None:
            return apology("invalid symbol", 400)

        # return redirect("/quoted")
        return render_template("quoted.html", name=quote["name"], price=usd(quote["price"]), symbol=quote["symbol"])

    else:
        return render_template("quote.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        username = request.form.get("username")
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        password = request.form.get("password")
        if not password:
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        confirmation = request.form.get("confirmation")
        if not confirmation:
            return apology("must provide confirmation", 400)

        elif not password == confirmation:
            return apology("must match the passwords", 400)


        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username is not exists
        if len(rows) != 0:
            return apology("existing username", 400)

        hashedpw = generate_password_hash(password)
        # insert data
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashedpw)

        # Redirect user to home page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # Get user's assets info
    user_id = session['user_id']
    assets = db.execute("SELECT * FROM assets WHERE user_id = ?", user_id)

    if request.method == "POST":
        # Ensure username was submitted
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("must provide symbol", 400)

        # Ensure share was submitted
        shares = request.form.get("shares")
        if not shares:
            return apology("must provide shares", 400)

        # Ensure shares was positive integer
        if is_positive_int(float(shares)) == False:
            return apology("must provide positive integer for shares", 400)

        shares = int(shares)

        # Ensure if the user holds the share of the symbol
        symbols = [a_dict["symbol"] for a_dict in assets]
        if not symbol in symbols:
            return apology("provide symbol from your assets", 400)

        #Render an apology if the input is not a positive integer or if the user does not own that many shares of the stock.
        current_share = db.execute("SELECT shares FROM assets WHERE user_id = ? and symbol = ?", user_id, symbol)[0]["shares"]
        final_share = current_share - shares

        if final_share < 0:
            return apology("must provide less than or equal to current number of shares", 400)

        #Insert transaction data to transactions table
        price = lookup(symbol)["price"]
        buy = False
        db.execute("INSERT INTO transactions (symbol, price, shares, buy, user_id) VALUES (?, ?, ?, ?, ?)", symbol, price, shares, buy, user_id)

        #Update the latest chsh after the transaction
        cash_list = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        cash = cash_list[0]["cash"]
        final_cash = shares * price + cash

        db.execute("UPDATE users SET cash = ? WHERE id = ?", final_cash, user_id)

        #if final_share is 0, delete the stock from assets table
        if final_share == 0:
            db.execute("DELETE FROM assets WHERE user_id = ? and symbol = ?", user_id, symbol)

        #Update the latest shares after the transaction
        else:
            db.execute("UPDATE assets SET shares = ? WHERE user_id = ? and symbol = ?", final_share, user_id, symbol)

        return redirect("/")

    else:
        #Get user's assets info
        asset_num = len(assets)

        return render_template("sell.html", assets=assets, asset_num=asset_num)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

