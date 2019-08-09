import os, requests

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
goodReadsUrl='https://www.goodreads.com/book/review_counts.json'
goodReadKey="R8JVn8Vq2SAR2QIjGgCEtg"


@app.route("/")
def index():
    if session.get("email") is None:
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
            session["email"] = user.email
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

@app.route("/book/<string:isbn>", methods=["GET", "POST"])
def book(isbn):
    if session.get("email") is None:
        return render_template( "authenticate.html", message="Please log in" )

    if request.method == "POST":
        rating = request.form.get("rating")
        review = request.form.get("review")
        db.execute("INSERT INTO reviews (isbn, email, rating, review) VALUES (:isbn, :email, :rating, :review)",
                   {"isbn": isbn, "email": session["email"], "rating": rating, "review": review})
        db.commit()

    # Get info from local DATABASE
    lBookReviews=db.execute("SELECT b.isbn, b.title, b.author, b.year, r.email, r.review, r.rating, r.updated FROM books b LEFT JOIN reviews r ON (b.isbn=r.isbn) WHERE (b.isbn = :isbn)", {"isbn": isbn}).fetchall()
    if (lBookReviews[0].email==None):
        session["message"]="No Local Reviews. "
    else:
        session["message"]='Local Reviews'

    # Get info from Good Read
    gBookReviews=requests.get(goodReadsUrl, params={"key": goodReadKey, "isbns": isbn})
    if gBookReviews.status_code == 404:
        session["message"]=session["message"]+"No response from Goodreads"
    else:
        average_rating=gBookReviews.json()['books'][0]['average_rating']
        ratings_count=gBookReviews.json()['books'][0]['ratings_count']

    header={'isbn': isbn, 'title': lBookReviews[0].title, 'author': lBookReviews[0].author, 'year': lBookReviews[0].year,
            'average_rating': average_rating, 'ratings_count': ratings_count}
    return render_template( "book.html", lBookReviews=lBookReviews, header=header, message=session.get("message") )
