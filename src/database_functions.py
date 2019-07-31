# coding=utf-8

import configparser

import mysql.connector

from parse_strings import (generate_query_string)


def choose_database(db):
    config = configparser.ConfigParser()
    config.read('config.ini')

    if db == 'auth':
        db = mysql.connector.connect(
            host=config['MySQL Auth']['host'],
            port=config['MySQL Auth']['port'],
            user=config['MySQL Auth']['user'],
            passwd=config['MySQL Auth']['passwd'],
            database=config['MySQL Auth']['database']
        )

    if db == 'testdb':
        db = mysql.connector.connect(
            host=config['MySQL Data']['host'],
            port=config['MySQL Data']['port'],
            user=config['MySQL Data']['user'],
            passwd=config['MySQL Data']['passwd'],
            database=config['MySQL Data']['database']
        )

    return db


def add_entry(db, table, entry, values, valuecnt=None):
    mycursor = db.cursor()

    if isinstance(values, int):
        valcountstr = "VALUES ("
        sql = "INSERT INTO " + table + " " + entry + " " + valcountstr + str(values) + ")"
        mycursor.execute(sql)
    else:
        sql = "INSERT INTO " + table + " " + entry + " " + "VALUES ('" + str(values) + "')"
        mycursor.execute(sql, values)

    db.commit()


def add_game(db, table, entry, values):
    mycursor = db.cursor()
    valcountstr = "VALUES ("
    sql = "INSERT INTO " + table + " " + entry + " " + valcountstr + values + ")"
    mycursor.execute(sql)

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


def search_entries_by_user(db, table, owner):
    mycursor = db.cursor()

    sql = "SELECT * FROM " + table + " WHERE owner LIKE \'%" + owner + "%\'"
    mycursor.execute(sql)
    result = mycursor.fetchall()

    return result

def search_expansions_by_game(db, table, owner, title):
    mycursor = db.cursor()
    uuid = search_uuid(owner, title)
    if uuid:
        sql = "SELECT * FROM " + table + " WHERE owner LIKE \'%" + owner + "%\' AND basegame_uuid=\'" + uuid + "\'"
        mycursor.execute(sql)
        result = mycursor.fetchall()

    return result

def search_uuid(owner, title):
    db = choose_database("testdb")
    mycursor = db.cursor()
    sql = "SELECT game_uuid FROM games WHERE owner LIKE \'%" + owner + "%\' AND title=\'" + title + "\'"
    mycursor.execute(sql)
    result = mycursor.fetchall()
    if len(result) > 0:
        return result[0][0]
    else:
        return None


# Selects entries from column in table where owner is owner
# and the playercount is >= the participants
# as of now, this is used for boardgames only,
# but it could be useful for expansions as well
def get_playable_entries(db, table, column, owner, no_participants=None, uuid=None):
    mycursor = db.cursor()

    if table == "games":
        where = "owner LIKE \'%" + owner + "%\' AND playercount>=" + str(no_participants)
    elif table == "expansions":
        where = "owner LIKE \'%" + owner + "%\' AND basegame_uuid=\'" + uuid + "\'"
    sql = "SELECT " + column + " FROM " + table + " WHERE " + where
    print(sql)
    mycursor.execute(sql)
    result = mycursor.fetchall()

    return result


def add_game_into_db(values):
    entry = "(owner, title, playercount, game_uuid)"
    add_game(choose_database("testdb"), "games", entry, values)


def add_multiple_games_into_db(csv_string):
    for _ in range(len(csv_string)):
        add_game_into_db(generate_query_string(csv_string[_]))


def add_expansion_into_db(values):
    entry = "(owner, basegame_uuid, title)"
    add_game(choose_database("testdb"), "expansions", entry, values) # using add_game because add_entry does not work...


def add_user_auth(user):
    entry = "(id)"
    add_entry(choose_database("auth"), "users", entry, user, 1)


def add_household(user1, user2):
    entry = '(user_ids)'
    household = user1 + ' ' + user2
    add_entry(choose_database("testdb"), "households", entry, household, 1)


# Is the user authenticated?
def check_user(user):
    result_user = search_single_entry(choose_database("auth"), "users", "id", user)

    if len(result_user) == 0:
        return 0
    else:
        return 1


# Does the user live together with another one?
# Either both or only his name is returned
def check_household(user):
    users_string = search_single_entry_substring(choose_database("testdb"), "households", "user_ids", user)

    if len(users_string) == 0:
        return user
    else:
        return users_string[0][0]
