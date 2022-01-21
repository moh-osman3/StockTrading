from flask import Flask, render_template, request
import sqlite3
from sqlite3 import Error

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
            CREATE TABLE users (
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
    return render_template("index.html")

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
            print(dct[key])
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

         
          

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
