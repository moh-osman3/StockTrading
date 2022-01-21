from flask import Flask, render_template
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
                balance FLOAT
            )
            ''')
db.commit()

@app.route("/")

def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    return render_template("signup.html")

if __name__ == "__main__":
    app.run(debug=True)
