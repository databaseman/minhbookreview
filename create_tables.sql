
Install postgres and misc associated lib
sudo su -
apt-get install postgresql postgresql-contrib
su - postgres  #log in as the oracle user
psql  #sqlplus
\q # exit sqlplus

Create postgres user shine
postgres@Ubuntu18Base:~$ createuser --interactive --pwprompt
Enter name of role to add: shine
Enter password for new role:
Enter it again:
Shall the new role be a superuser? (y/n) y

You should be able to see the user in the db now:
postgres@Ubuntu18Base:~$ psql
postgres=# \du
                                   List of roles
 Role name |                         Attributes                         | Member of
-----------+------------------------------------------------------------+-----------
 postgres  | Superuser, Create role, Create DB, Replication, Bypass RLS | {}
 shine     | Superuser, Create role, Create DB                          | {}

Create db under that new user:
postgres=# create database bookreview owner=shine;
CREATE DATABASE
postgres=# \l
                                  List of databases
    Name    |  Owner   | Encoding |   Collate   |    Ctype    |   Access privileges
------------+----------+----------+-------------+-------------+-----------------------
 bookreview | shine    | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
 postgres   | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
 template0  | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
            |          |          |             |             | postgres=CTc/postgres
 template1  | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
            |          |          |             |             | postgres=CTc/postgres
(4 rows)

Log into that db (without a corresponding shine unix user)
postgres@Ubuntu18Base:~$ psql --host=localhost --dbname=bookreview --username=shine

If you want to log in using "psql -U shine" then you need to create a unix user first
	adduser shine
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email    VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    created  DATE NOT NULL DEFAULT NOW(),
    updated   DATE NOT NULL DEFAULT NOW(),
    deleted  DATE DEFAULT NULL
);

CREATE TABLE books (
    isbn     VARCHAR PRIMARY KEY,
    title    VARCHAR NOT NULL,
    author   VARCHAR NOT NULL,
    year     SMALLINT NOT NULL,
    created  DATE NOT NULL DEFAULT NOW(),
    updated   DATE NOT NULL DEFAULT NOW(),
    deleted  DATE DEFAULT NULL
);

CREATE TABLE reviews (
    isbn     VARCHAR NOT NULL,
    email    VARCHAR NOT NULL,
    review   VARCHAR,
    rating   SMALLINT NOT NULL,
    created  DATE NOT NULL DEFAULT NOW(),
    updated   DATE NOT NULL DEFAULT NOW(),
    deleted  DATE DEFAULT NULL,
    PRIMARY KEY (isbn, email)
);

bookreview=# \d
List of relations
Schema |       Name        |   Type   | Owner
--------+-------------------+----------+-------
public | books             | table    | shine
public | reviews           | table    | shine
public | users             | table    | shine
public | users_id_seq      | sequence | shine
(4 rows)


bookreview=# \d books
                     Table "public.books"
 Column  |       Type        | Collation | Nullable | Default
---------+-------------------+-----------+----------+---------
 isbn    | character varying |           | not null |
 title   | character varying |           | not null |
 author  | character varying |           | not null |
 year    | smallint          |           | not null |
 created | date              |           | not null | now()
 updated | date              |           | not null | now()
 deleted | date              |           |          |
Indexes:
    "books_pkey" PRIMARY KEY, btree (isbn)

bookreview=# \d users
                                  Table "public.users"
  Column  |       Type        | Collation | Nullable |              Default
----------+-------------------+-----------+----------+-----------------------------------
 id       | integer           |           | not null | nextval('users_id_seq'::regclass)
 username | character varying |           | not null |
 password | character varying |           | not null |
 created  | date              |           | not null | now()
 updated  | date              |           | not null | now()
 deleted  | date              |           |          |
Indexes:
    "users_pkey" PRIMARY KEY, btree (id)

    bookreview=# \d reviews
                    Table "public.reviews"
 Column  |       Type        | Collation | Nullable | Default
---------+-------------------+-----------+----------+---------
 isbn    | character varying |           | not null |
 email   | character varying |           | not null |
 review  | character varying |           |          |
 rating  | smallint          |           | not null |
 created | date              |           | not null | now()
 updated | date              |           | not null | now()
 deleted | date              |           |          |
Indexes:
    "reviews_pkey" PRIMARY KEY, btree (isbn, email)

export DATABASE_URL=postgres://shine:shine@localhost/bookreview
export FLASK_APP=application.py
export FLASK_DEBUG=1

python3 import.py  # make sure you remove the header before import or skip it duriing import
