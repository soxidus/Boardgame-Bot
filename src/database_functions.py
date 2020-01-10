# coding=utf-8

import configparser
import os

import mysql.connector

from parse_strings import (generate_query_string)


def choose_database(db):
    config = configparser.ConfigParser()
    config_path = os.path.dirname(os.path.realpath(__file__))
    config.read(os.path.join(config_path, "config.ini"))

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
    # wait, aren't these exactly the same? Do we still need this if/else?
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
        if not result:  # no expansions
            return None
        return result
    return False


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
def get_playable_entries(db, table, column, owner, no_participants=0, uuid=None):
    mycursor = db.cursor()

    if table == "games":
        where = "owner LIKE \'%" + owner + "%\' AND playercount>=" + str(no_participants)
    elif table == "expansions":
        where = "owner LIKE \'%" + owner + "%\' AND basegame_uuid=\'" + uuid + "\'"
    sql = "SELECT " + column + " FROM " + table + " WHERE " + where
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


# variable names user1 and user2 are a bit arbitrary
# user2 can hold more than one username
def add_household(users):
    entry = '(user_ids)'
    household = ' '.join(users)
    for u in users:
        res = check_household(u)
        if res != u:  # user already lives with someone, delete it
            delete_single_entry_substring(choose_database("testdb"), "households", entry, u)
    add_entry(choose_database("testdb"), "households", entry, household, 1)
    update_household_games(users)


def delete_single_entry_substring(db, table, entry, value):
    mycursor = db.cursor()
    sql = "DELETE FROM " + table + " WHERE " + entry + " LIKE \'%" + value + "%\'"
    mycursor.execute(sql)

    db.commit()


def update_household_games(users):
    household = ' '.join(users)
    db = choose_database("testdb")
    mycursor = db.cursor()
    for u in users:
        sql = "UPDATE games SET owner='" + str(household) + "' WHERE owner LIKE \'%" + str(u) + "%\' AND NOT owner='" + str(household) + "'"
        mycursor.execute(sql)
    db.commit()


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
