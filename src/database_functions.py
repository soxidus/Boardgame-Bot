# coding=utf-8

import mysql.connector


def choose_database(db):
    if db == 'auth':
        db = mysql.connector.connect(
            host="localhost",
            user="testuser",
            passwd="password",
            database="auth"
        )

    if db == 'testdb':
        db = mysql.connector.connect(
            host="localhost",
            user="testuser",
            passwd="password",
            database="testdb"
        )

    return db


def add_entry(db, table, entry, values):
    mycursor = db.cursor()

    if isinstance(values, int):
        valcountstr = "VALUES ("
        sql = "INSERT INTO " + table + " " + entry + " " + valcountstr + str(values) + ")"
        mycursor.execute(sql)
    else:
        valcountstr = "VALUES (%s"
        for _ in range(len(values)-1):
            valcountstr += ",%s "
        sql = "INSERT INTO " + table + " " + entry + " " + valcountstr + ")"
        mycursor.execute(sql, values)

    db.commit()


def add_game_into_db(values):
    entry = "(title, owner, playercount)"
    add_entry(choose_database("testdb"), "games", entry, values)


def add_expansion_into_db(values):
    entry = "(title, owner, basegame)"
    add_entry(choose_database("testdb"), "games", entry, values)


def add_user_auth(user):
    entry = "(id)"
    add_entry(choose_database("auth"), "users", entry, user)

