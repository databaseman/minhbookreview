#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Purpose: Book Reviews

Input for Web:
    ISBN/ Title / Author for search criterias
    Rating & Review for books (only 1 review per user per book)

Output for Web:
    ISBN + Title + Author + Published Year + Reviews +
    GoodReads average ratings & counts

Input for API:
    ISBN

Output for API:
    {
        "title": "Memory",
        "author": "Doug Lloyd",
        "year": 2015,
        "isbn": "1632168146",
        "review_count": 28,
        "average_score": 5.0
    }

Usage:
    export DATABASE_URL=postgres://shine:shine@localhost/bookreview
    export FLASK_APP=application.py
    export FLASK_DEBUG=1
    $ python application.py
    http://127.0.0.1:5000/  #require login with an account
    http://127.0.0.1:5000/api/<ISBN>  #no login needed

Notes:
    DB 'bookreview' is local Postgres.
    DB and Tables are under the 'shine' user.
    Info about the users/books/reviews tables are in the create_tables.sql
    books table was imported using the import.py and books.csv files

History:
    08/13/2019 Minh Nguyen    Created
"""
import os, requests

from flask import Flask, render_template, request, redirect, session, url_for, jsonify
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
    # User must log in before able to do book search
    if session.get("email") is None:
        return render_template( "authenticate.html", message=session.get("message") )
    else:
        return render_template("booksearch.html")

@app.route("/authentication", methods=["POST"])
def authenticate():
    # User can log in or register as new user
    email=request.form.get("email")
    password=request.form.get("password")
    if request.form.get("action") == 'Login':
        user=db.execute("SELECT * FROM users WHERE email = :email and password = :password", {"email": email, "password": password}).fetchone()
        if (user is None):
            session["message"]="No such user / invalid password."
        else:
            session["message"]=''
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
    email=session.get("email")
    if  email is None:
        return render_template( "authenticate.html", message="Please log in" )

    if request.method == "POST":
        rating = request.form.get("rating")
        review = request.form.get("review")
        #Only 1 review per user is allow
        if (db.execute("SELECT * FROM reviews WHERE isbn=:isbn AND email=:email", {"isbn": isbn, "email": email}).rowcount == 0):
            db.execute("INSERT INTO reviews (isbn, email, rating, review) VALUES (:isbn, :email, :rating, :review)",
                       {"isbn": isbn, "email": email, "rating": rating, "review": review})
        else:
            db.execute("UPDATE reviews SET rating=:rating, review=:review, updated=now() WHERE isbn=:isbn AND email=:email",
                       {"isbn": isbn, "email": email, "rating": rating, "review": review})
        db.commit()

    # Get info from local DATABASE
    lBookReviews=db.execute("SELECT b.isbn, b.title, b.author, b.year, r.email, r.review, r.rating, r.updated FROM books b LEFT JOIN reviews r ON (b.isbn=r.isbn) WHERE (b.isbn = :isbn)", {"isbn": isbn}).fetchall()

    # Get info from Goodreads
    gBookReviews=requests.get(goodReadsUrl, params={"key": goodReadKey, "isbns": isbn})
    if gBookReviews.status_code != 200:
        session["message"]=session["message"]+"Problem with Goodreads. Status Code: "+str(gBookReviews.status_code)
    else:
        session["message"]=''
        average_rating=gBookReviews.json()['books'][0]['average_rating']
        ratings_count=gBookReviews.json()['books'][0]['ratings_count']

    header={'isbn': isbn, 'title': lBookReviews[0].title, 'author': lBookReviews[0].author, 'year': lBookReviews[0].year,
            'average_rating': average_rating, 'ratings_count': ratings_count}
    return render_template( "book.html", lBookReviews=lBookReviews, header=header, message=session.get("message") )

@app.route("/api/<string:isbn>")
def book_api(isbn):
    # Get info from local DATABASE
    lBook=db.execute("SELECT isbn, title, author, year FROM books WHERE (isbn = :isbn)", {"isbn": isbn}).fetchone()
    if (lBook is None):
        return jsonify({"error": "Invalid ISBN"}), 422

    # Get info from Good Read
    gBookReviews=requests.get(goodReadsUrl, params={"key": goodReadKey, "isbns": isbn})
    if gBookReviews.status_code != 200:
        session["message"]=session["message"]+"Problem with Goodreads. Status Code: "+str(gBookReviews.status_code)
    else:
        average_rating=gBookReviews.json()['books'][0]['average_rating']
        ratings_count=gBookReviews.json()['books'][0]['ratings_count']

    return jsonify({
                    'isbn': isbn,
                    'title': lBook.title,
                    'author': lBook.author,
                    'year': lBook.year,
                    'average_rating': average_rating,
                    'ratings_count': ratings_count
                })
