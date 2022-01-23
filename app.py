from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from sqlite3 import Error
from lookup import get_stock_data

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key="secret_key"
app.config['SESSION_TYPE'] = 'filesystem'

ERR_USER_NOT_FOUND = "Username not found!"

# sqlite database setup to store all users with accounts on record
def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print("The error {} occurred".format(e))

    return connection

db = create_connection("users.db")
cur = db.cursor()

cur.execute('''
            CREATE TABLE if not exists users (
                id INT PRIMARY KEY,
                fname varchar(255),
                lname varchar(255),
                email varchar(400),
                username varchar(255),
                password varchar(255),
                balance FLOAT
            )
            ''')

db.commit()

@app.route("/")
def index():
    if "user" not in session or session["user"] == None:
        session["user"] = None
        return render_template("index.html",
           display="Sign up or Login to start trading today!")

    return render_template("index.html",
       display="Welcome, {}!".format(session["user"]))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    dct = {}
    # keys associated with database row
    keys = ["fname", "lname", "email", "username", "password", "balance"]

    with sqlite3.connect("users.db") as db:
        cur = db.cursor()

        # find highest valid id in table 
        cur.execute("SELECT max(id) FROM users")
        lastid = cur.fetchone()[0]
        if lastid == None:
            lastid = -1
        dct["id"] = lastid + 1

        for key in keys:
            dct[key] = request.form.get(key)
            # check that usernames and password are valud
            if key == "password":
                if dct[key] != request.form.get("confirm-password"):
                    return render_template("error.html", error="Make sure your passwords match!")
            if key == "username":
                cur.execute("SELECT username FROM users WHERE username='{}'".format(dct[key]))
                if len(cur.fetchall()) > 0:
                    return render_template("error.html", error="Username already exists!")

        cur.execute("INSERT INTO users VALUES {}".format(tuple(dct.values())))
        # for testing -- checking the rows in my db
        for row in cur.execute("SELECT * FROM users"):
            print(row)     
        db.commit()
    session["user"] = dct["username"]

    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    with sqlite3.connect("users.db") as db:
        cur = db.cursor()
        username = request.form.get("username")
        password = request.form.get("password")

        cur.execute("SELECT password FROM users WHERE username='{}'".format(username))

        fetched = cur.fetchone()
        if fetched == None:
            return render_template("error.html", error=ERR_USER_NOT_FOUND) 

        password_from_db = fetched[0]

        if password_from_db == None:
            return render_template("error.html", error=ERR_USER_NOT_FOUND) 

        if password_from_db != password:
            return render_template("error.html", error="The username and password entered do not match!")

        session['user'] = username
        session['logged_in'] = True

    print(session['user'])
    return redirect('/')

    
@app.route("/logout")
def logout():
    session['user'] = None
    return redirect("/")

@app.route("/buy", methods=["GET", "POST"])
def request_transaction():
    # make sure user is logged in before they can buy
    print(request.url_rule)
    if session["user"] == None:
        return render_template("error.html", error="Please sign up or log in")

    if request.method == "GET":
        return render_template("buy.html")
    
    requested_symbol = request.form.get("stock-symbol")
    num_shares = request.form.get("numshares")
    quote = get_stock_data(requested_symbol)
    print(quote)

    return redirect(url_for("quote", name=quote["name"], price=quote["price"],
                    symbol=quote["symbol"], shares=num_shares))


@app.route("/quote", methods=["GET", "POST"])
def quote():
    name = request.args["name"]
    price = float(request.args["price"])
    symbol = request.args["symbol"]
    shares = float(request.args["shares"])
    cost = shares * price

    if request.method == "GET":
        return render_template("quote.html", name=name, price=price,
                               symbol=symbol, shares=shares, cost=cost)

    print(session["user"])
    # update balances in global table. 
    with sqlite3.connect("users.db") as db:
        cur = db.cursor()
        cur.execute("SELECT balance FROM users WHERE username='{}'".format(session["user"]))
        fetch = cur.fetchone()
        if fetch == None:
            return render_template("error.html", error=ERR_USER_NOT_FOUND)

        cur_balance = fetch[0]

        if cur_balance == None:
            return render_template("error.html", error=ERR_USER_NOT_FOUND)
        print(cur_balance)

        # make sure the transaction is valid
        if cost > cur_balance:
            return render_template("error.html", error="Balance is too low to complete transaction!")
        
        cur.execute("UPDATE users SET balance='{}' WHERE username='{}'".format(cur_balance - cost, session["user"]))
        db.commit()
    

        print(f"UPDATE {session['user']} SET numshares='{shares}',"
              f"costper='{price}', totalcost='{cost}'")
    # create a table for the specific user if one does not already exist
    with sqlite3.connect("users.db") as db:
        cur = db.cursor()

        cur.execute(f"CREATE TABLE if not exists {session['user']} ("
                     "symbol VARCHAR(255) PRIMARY KEY,"
                     "numshares INT,"
                     "avgcostper FLOAT,"
                     "totalcost FLOAT,"
                     "return FLOAT)")

        # I expect there is a more succinct way to run the below queries
        # i.e INSERT OR UPDATE if symbol is in table
        cur.execute(f"SELECT totalcost, numshares FROM {session['user']} "
                    f"WHERE symbol='{symbol}'")
        fetch = cur.fetchall()
        print(fetch)
        # if symbol is not found in table (first time buying stock)
        if fetch == []:
            cur.execute(f"INSERT INTO {session['user']} VALUES "
                        f"('{symbol}', '{shares}', '{price}', '{cost}', '{0}')")
        else:   
            cur_total = fetch[0][0]
            cur_shares = fetch[0][1]
            total_cost = cur_total + cost # amt paid for shares
            total_shares = shares + cur_shares
            avgper = total_cost / total_shares # avg cost per share
            total_value = price * total_shares # current market value of stocks
            print(total_value)
            print(total_cost)
            return_on_invest = total_value - total_cost
            print(f"cur total: {cur_total}, {cur_shares}")

            cur.execute(f"UPDATE {session['user']} "
                        f"SET numshares='{total_shares}', "
                        f"avgcostper='{total_shares}', "
                        f"totalcost='{total_cost}', "
                        f"return='{return_on_invest}'")
        
        for row in cur.execute(f"SELECT * FROM {session['user']}"):
            print(row)
        db.commit()

        


    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
    session["user"] = None
