import os

from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":
        email=request.form.get("email")
        password=request.form.get("password")
        if request.form.get("action") == 'Login':
            if (db.execute("SELECT * FROM users WHERE email = :email and password = :password", {"email": email, "password": password}).rowcount == 0):
                return render_template("error.html", message="No such user / invalid password.")
            else:
                return render_template("booksearch.html")
        else: #Register
            if (db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).rowcount > 0):
                return render_template("error.html", message="User already registered.")
            else:
                db.execute("INSERT INTO users (email, password) VALUES (:email, :password)",{"email": email, "password": password})
                db.commit()
                return render_template("booksearch.html")
    return render_template("index.html")

@app.route("/booksearch", methods=["POST"])
def booksearch():
    isbn=request.form.get("isbn")+'%'
    title=request.form.get("title")+'%'
    author=request.form.get("author")+'%'
    booklist=db.execute("SELECT * FROM books WHERE (isbn like :isbn) and (title like :title) and (author like :author)",
                         {"isbn": isbn, "title": title, "author": author}).fetchall()
    return render_template("booklist.html", booklist=booklist)
