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
    #    mycursor = db.cursor()
    valcountstr = "VALUES (%s"

    for _ in range(len(values)-1):
        valcountstr += ",%s "

    sql = "INSERT INTO " + table + " " + entry + " " + valcountstr + ")"

#   might need parsing
#    mycursor.execute(sql, values)

#    db.commit()


def add_game_into_db(values):
    entry = "(\"title\", \"owner\", \"playercount\")"
    add_entry(choose_database("testdb"), "games", entry, values)


def add_expansion_into_db(values):
    entry = "(\"title\", \"owner\", \"basegame\")"
    add_entry(choose_database("testdb"), "games", entry, values)
