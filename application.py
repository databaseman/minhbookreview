import os

from flask import Flask, render_template, request, redirect, session, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    if session.get("user_id") is None:
        return render_template( "authenticate.html", message=session.get("message") )
    else:
        return render_template("booksearch.html")

@app.route("/authentication", methods=["POST"])
def authenticate():
    email=request.form.get("email")
    password=request.form.get("password")
    if request.form.get("action") == 'Login':
        user=db.execute("SELECT * FROM users WHERE email = :email and password = :password", {"email": email, "password": password}).fetchone()
        if (user is None):
            session["message"]="No such user / invalid password."
        else:
            session["user_id"] = user.id
    else: #Register
        user=db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).fetchone()
        if (user is not None):
            session["message"]=email+" user already registered."
        else:
            db.execute("INSERT INTO users (email, password) VALUES (:email, :password)",{"email": email, "password": password})
            db.commit()
            session["message"]="User has been added. Please log in"
    return redirect( url_for("index", message=session.get("message")) )

@app.route("/booksearch", methods=["POST"])
def booksearch():
    isbn=request.form.get("isbn")+'%'
    title=request.form.get("title")+'%'
    author=request.form.get("author")+'%'
    booklist=db.execute("SELECT * FROM books WHERE (isbn like :isbn) and (title like :title) and (author like :author)",
                         {"isbn": isbn, "title": title, "author": author}).fetchall()
    if (booklist == []):
        session["message"]="Selection Not found. isbn:{} title:{} author:{}".format(isbn, title, author)
    else:
        session["message"]=''
    return render_template("booklist.html", booklist=booklist, message=session["message"])

@app.route("/book/<string:isbn>")
def book(isbn):
    # Get info from local DATABASE
    lBookReviews=db.execute("SELECT b.isbn, b.title, b.author, b.year, r.email, r.review, r.rating, r.updated FROM books b LEFT JOIN reviews r ON (b.isbn=r.isbn) WHERE (b.isbn = :isbn)", {"isbn": isbn}).fetchall()
    if (lBookReviews[0].email==None):
        session["message"]="No Local Reviews. "
    else:
        session["message"]='Local Reviews'
    header={'isbn': isbn, 'title': lBookReviews[0].title, 'author': lBookReviews[0].author, 'year': lBookReviews[0].year}
    # Get info from Good Read
    return render_template( "book.html", lBookReviews=lBookReviews, header=header, message=session.get("message") )
