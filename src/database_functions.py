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
