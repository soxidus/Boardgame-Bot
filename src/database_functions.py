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
        for _ in range(len(values) - 1):
            valcountstr += ",%s "
        sql = "INSERT INTO " + table + " " + entry + " " + valcountstr + ")"
        mycursor.execute(sql, values)

    db.commit()


def search_single_entry(db, table, entry, values):
    mycursor = db.cursor()

    if isinstance(values, int):
        sql = "SELECT * FROM " + table + " WHERE " + entry + " = " + str(values)
        mycursor.execute(sql)
    if isinstance(values, str):
        sql = "SELECT * FROM " + table + " WHERE " + entry + " = " + str(values)
        mycursor.execute(sql)
    else:
        pass

    result = mycursor.fetchall()

    return result


def search_single_entry_substring(db, table, entry, values):
    mycursor = db.cursor()

    if isinstance(values, int):
        sql = "SELECT * FROM " + table + " WHERE " + entry + " LIKE \'%" + str(values) + "%\'"
        mycursor.execute(sql)
    if isinstance(values, str):
        sql = "SELECT * FROM " + table + " WHERE " + entry + " LIKE \'%" + str(values) + "%\'"
        mycursor.execute(sql)
    else:
        pass
    result = mycursor.fetchall()

    return result


def add_game_into_db(values):
    entry = "(title, owner, playercount)"
    add_entry(choose_database("testdb"), "games", entry, values)


def add_expansion_into_db(values):
    entry = "(title, owner, basegame)"
    add_entry(choose_database("testdb"), "games", entry, values)


def add_user_auth(user):
    entry = "(id)"
    add_entry(choose_database("auth"), "users", entry, user)


def check_user(user):
    result_user = search_single_entry(choose_database("auth"), "users", "id", user)

    if len(result_user) == 0:
        return 0
    else:
        return 1


def check_household(user):
    users_string = search_single_entry_substring(choose_database("testdb"), "households", "user_ids", user)

    if len(users_string) == 0:
        return user
    else:
        return users_string
