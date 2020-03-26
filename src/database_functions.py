# coding=utf-8

import configparser
import os
import datetime

import mysql.connector

from parse_strings import (parse_game_values_from_array, generate_uuid_32)


# GENERAL TODO: Use column instead of entry?
# GENERAL TODO: Specify DB and table within function if possible? At least find a uniform way!
# GENERAL TODO: Delete str()-conversion where we definitely already use type str!
# NOTE: fct names containing "single_entry" seem to only want ONE column name as a parameter - slightly misleading
# GENERAL TODO: Reorder functions by elementality

def choose_database(db):
    """Connect MYSQL connector to database 'auth' or 'datadb'."""
    config = configparser.ConfigParser()
    config_path = os.path.dirname(os.path.realpath(__file__))
    config.read(os.path.join(config_path, "config.ini"))

    if db == 'auth':
        db = mysql.connector.connect(
            host=config['MySQL Auth']['host'],
            # port=config['MySQL Auth']['port'],
            user=config['MySQL Auth']['user'],
            passwd=config['MySQL Auth']['passwd'],
            database=config['MySQL Auth']['database']
        )

    if db == 'datadb':
        db = mysql.connector.connect(
            host=config['MySQL Data']['host'],
            # port=config['MySQL Data']['port'],
            user=config['MySQL Data']['user'],
            passwd=config['MySQL Data']['passwd'],
            database=config['MySQL Data']['database']
        )

    return db


def add_entry(db, table, entry, values, valuesformatted=None):
    """Add one entry to a database.

    Parameters
    ----------
    db : MySQLConnection
        connection to database
    table : str
        table to add entry to
    entry : str
        SQL compliant list of columns
    values : list or str
        array or SQL compliant list of values
    valuesformatted : NoneType or Boolean
        if True, values should be an SQL compliant list of values
    """
    mycursor = db.cursor()

    if valuesformatted:
        sql = "INSERT INTO " + table + " " + entry + " " + "VALUES " + str(values)
        mycursor.execute(sql)
    elif isinstance(values, int):
        valcountstr = "VALUES ("
        sql = "INSERT INTO " + table + " " + entry + " " + valcountstr + str(values) + ")"
        mycursor.execute(sql)
    else:
        sql = "INSERT INTO " + table + " " + entry + " " + "VALUES ('" + str(values) + "')"
        mycursor.execute(sql, values)

    db.commit()


def add_game(db, table, entry, values):
    """Add a game into a database.

    Parameters
    ----------
    db : MySQLConnection
        connection to database
    table : str
        table to add game to (typically "games" or "expansions")
    entry : str
        SQL compliant list of columns
    values : str
        SQL compliant list of values
    """
    mycursor = db.cursor()
    valcountstr = "VALUES ("
    sql = "INSERT INTO " + table + " " + entry + " " + valcountstr + values + ")"
    mycursor.execute(sql)

    db.commit()


# TODO: I'm VERY unsure this can actually be used with more than 1 value since that would need an AND
def search_single_entry(db, table, entry, values, valuecnt=None):
    """Search all values from a table by constraint.

    Parameters
    ----------
    db : MySQLConnection
        connection to a database
    table : str
        table to search
    entry : str
        SQL compliant list of columns
    values : int or str
        if of type str and more than one value is passed, specify valuecnt and separate values with commas
    valuecnt : NoneType or int
        number of values passed

    Returns
    -------
    result : list of tuples
        Rows from <table> where <entry> is <values>
    """
    mycursor = db.cursor()
    if isinstance(values, int):
        sql = "SELECT * FROM " + table + " WHERE " + entry + " = " + str(values)
        mycursor.execute(sql)
    if isinstance(values, str):
        if valuecnt and valuecnt > 1:
            sql = "SELECT * FROM " + table + " WHERE " + entry + " = " + str(values)
        else:
            sql = "SELECT * FROM " + table + " WHERE " + entry + " = '" + str(values) + "'"
        mycursor.execute(sql)
    else:
        pass

    result = mycursor.fetchall()

    return result


# TODO: Rename
def search_column(db, table, column):
    """Get contents of column(s) from table.

    Parameters
    ----------
    db : MySQLConnection
        connection to database
    table : str
    column : str
        SQL compliant string of column(s)

    Returns
    -------
    result : list of tuples
        rows from db
    """
    mycursor = db.cursor()
    sql = "SELECT " + column + " FROM " + table
    mycursor.execute(sql)
    result = mycursor.fetchall()
    return result


# TODO: Rename values to value: only one can be tested, otherwise use "AND"
def search_column_with_constraint(db, table, column, entry, values):
    """Get contents of column(s) where condition applies.

    Parameters
    ----------
    db : MySQLConnection
        connection to database
    table : str
    column : str
    entry : str
        column to test condition on
    values : str
        value to test condition for

    Returns
    -------
    result : list of tuples
        contents of <column> where <entry> is <value>
    """
    mycursor = db.cursor()
    sql = "SELECT " + column + " FROM " + table + " WHERE " + entry + " = '" + str(values) + "'"
    mycursor.execute(sql)
    result = mycursor.fetchall()
    return result


# TODO: rename values to substring?
def search_single_entry_substring(db, table, entry, values):
    """Get entries where a substring is contained.

    Parameters
    ----------
    db : MySQLConnection
        connection to database
    table : str
    entry : str
        column to compare to substring
    values : str
        substring to compare to

    Returns
    -------
    result : list of tuples
    """
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


# TODO: rename
# it might be slightly unfortunate to name this function "by_user"
# when it's actually looking up the owner
def search_entries_by_user(db, table, owner):
    """Get all entries for a specific owner.

    Parameters
    ----------
    db : MySQLConnection
        connectin to database
    table : str
    owner : str

    Returns
    -------
    result : list of tuples
    """
    mycursor = db.cursor()

    sql = "SELECT * FROM " + table + " WHERE owner LIKE \'%" + owner + "%\'"
    mycursor.execute(sql)
    result = mycursor.fetchall()

    return result


def search_expansions_by_game(db, table, owner, title):
    """Return all expansions owned by a user for a specific game.

    Parameters
    ----------
    db : MySQLConnection
        connection to database
    table : str
    owner : str
    title : str
        the game's title

    Returns
    -------
    result : list of tuples or NoneType ore False
        if None, the user has no expansions for the game
        if False, the user doesn't own the game
    """
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


# TODO: here, db and table are set WITHIN the function - UNIFORMITY!
def search_uuid(owner, title):
    """Get UUID for a game owned by a specific user.

    Parameters
    ----------
    owner : str
    title : str
        the game's title

    Returns
    -------
    result : str or NoneType
        UUID of game, None if user doesn't own it
    """
    db = choose_database("datadb")
    mycursor = db.cursor()
    sql = "SELECT game_uuid FROM games WHERE owner LIKE \'%" + owner + "%\' AND title=\'" + title + "\'"
    mycursor.execute(sql)
    result = mycursor.fetchall()
    if len(result) > 0:
        return result[0][0]
    else:
        return None


def get_playable_entries(db, table, column, owner, no_participants=0, uuid=None, planned_date=None):
    """Get all playable games or expansions.

    Parameters
    ----------
    db : MySQLConnection
        connection to database
    table : str
        typically 'games' or 'expansions'
    column : str
        typically 'title'
    owner : str
    no_participants : int
        default is 0
    uuid : NoneType or str
        if looking at expansions, provide the basegame's UUID
    planned_date : NoneType or datetime.datetime

    Returns
    -------
    result : list of tuples
        either all games by this user that can be played with no_participants people and have last been played at least two weeks ago
        or all expansions by this user for the basegame specified
    """
    mycursor = db.cursor()

    if table == "games":
        where = "owner LIKE \'%" + owner + "%\' AND (playercount>=" + str(no_participants) + " OR playercount=\'X\')"
        if planned_date:
            delta = datetime.timedelta(weeks=2)
            not_played_after = planned_date - delta
            not_played_after = not_played_after.date()
            add_to_where = " AND (last_played<\'" + str(not_played_after) + "\' OR last_played IS NULL)"
            where += add_to_where
    elif table == "expansions":
        where = "owner LIKE \'%" + owner + "%\' AND basegame_uuid=\'" + uuid + "\'"
    sql = "SELECT " + column + " FROM " + table + " WHERE " + where

    mycursor.execute(sql)
    result = mycursor.fetchall()

    return result


def get_playable_entries_by_category(db, table, column, owner, category, no_participants=0, planned_date=None):
    """Get playable games in a category.

    Parameters
    ----------
    db : MySQLConnection
        connection to database
    table : str
        typically 'games'
    column : str
        typically 'title'
    owner : str
    category : str
    no_participants : int
        default is 0
    planned_date : NoneType or datetime.datetime

    Returns
    -------
    result : list of tuples
        all games owned by user in the specified category that can be played with no_participants people and
        have been last played at least two weeks ago
    """
    mycursor = db.cursor()

    where = "owner LIKE \'%" + owner + "%\' AND (playercount>=" + str(no_participants) + " OR playercount=\'X\')"
    if planned_date:
        delta = datetime.timedelta(weeks=2)
        not_played_after = planned_date - delta
        not_played_after = not_played_after.date()
        add_to_where = " AND (last_played<\'" + str(not_played_after) + "\' OR last_played IS NULL)"
        where += add_to_where

    on = table + ".game_uuid=categories.`"+category + "` AND " + where  # use `` bc. categories have spaces in them
    sql = "SELECT " + table + "." + column + " FROM " + table + " INNER JOIN categories ON " + on

    mycursor.execute(sql)
    result = mycursor.fetchall()

    return result


# TODO: again, table is specified WITHIN the function
def add_game_into_categories(db, categories, uuid):
    """Add a game into table 'categories'.

    Parameters
    ----------
    db : MySQLConnection
        connection to database
    categories : list
        list of categories this game belongs to
    uuid : str
    """
    entry = "("
    vals = "("
    for cat in categories:
        entry += "`" + cat + "`,"
        vals = vals + "'" + str(uuid) + "',"
    entry = entry[:-1] + ")"
    vals = vals[:-1] + ")"
    add_entry(db, "categories", entry, vals, valuesformatted=True)


# TODO: Again, this function specifies db and table INSIDE
def add_game_into_db(games_values, cats=None, uuid=None):
    """Add a game into database 'datadb'.

    Parameters
    ----------
    games_values : str
        SQL compliant list of values
    cats : NoneType or list
    uuid : NoneType or str
        needs to be specified if cats are given
    """
    entry = "(owner, title, playercount, game_uuid)"
    add_game(choose_database("datadb"), "games", entry, games_values)
    if cats and uuid:
        add_game_into_categories(choose_database("datadb"), cats, uuid)


def add_multiple_games_into_db(games_array):
    """Add multiple games into database 'datadb'.

    Parameters
    ----------
    games_array : list of lists
        rows contain all info on games
        columns correspond to owner, title, max. playercount, categories
    """
    for _ in range(len(games_array)):  # iterate through rows
        if len(games_array[_]) > 3:  # categories are given
            g_id = generate_uuid_32()
            try:
                add_game_into_db(parse_game_values_from_array(games_array[_][:3], uuid=g_id),
                                 cats=games_array[_][3:], uuid=g_id)
            except mysql.connector.IntegrityError:
                pass
        else:
            try:
                add_game_into_db(parse_game_values_from_array(games_array[_]))
            except mysql.connector.IntegrityError:
                pass


def add_expansion_into_db(values):
    """Add expansion into database 'datadb'.

    Parameters
    ----------
    values : str
        SQL compliant list of values for entries owner, basegame_uuid, title
    """
    entry = "(owner, basegame_uuid, title)"
    add_game(choose_database("datadb"), "expansions", entry, values)


def add_user_auth(user_id, name=None):
    """Record that a user authenticated, save their info.

    Parameters
    ----------
    user_id : int
        ChatID
    name : NoneType or str
        username, or alias
    """
    entry = "(id)"
    add_entry(choose_database("auth"), "users", entry, user_id)
    if name:  # use username for settings
        settings_entry = "(user)"
        add_entry(choose_database("datadb"), "settings", settings_entry, name)
    if user_id < 0:  # group
        settings_entry = "(id)"
        add_entry(choose_database("datadb"), "group_settings", settings_entry, user_id)


def add_household(users):
    """Update household info for users.
    Games owned by those users are updated with the new household info as well.

    Parameters
    ----------
    users : list
    """
    entry = '(user_ids)'
    household = ' '.join(users)
    for u in users:
        res = check_household(u)
        if res != u:  # user already lives with someone, delete it
            delete_single_entry_substring(choose_database("datadb"), "households", entry, u)
    add_entry(choose_database("datadb"), "households", entry, household)
    update_household_games(users)


# TODO: Rename value to substring?
def delete_single_entry_substring(db, table, entry, value):
    """Delete entries containing a substring.

    Parameters
    ----------
    db : MySQLConnection
        connection to database
    table : str
    entry : str
        column to test for substring
    value : str
        substring to compare to
    """
    mycursor = db.cursor()
    sql = "DELETE FROM " + table + " WHERE " + entry + " LIKE \'%" + value + "%\'"
    mycursor.execute(sql)

    db.commit()


# TODO: Again, db and table are specified WITHIN the function.
def update_household_games(users):
    """Update games' owners with new household info.

    Parameters
    ----------
    users : list
    """
    household = ' '.join(users)
    db = choose_database("datadb")
    mycursor = db.cursor()
    for u in users:
        sql = "UPDATE games SET owner='" + str(household) + "' WHERE owner LIKE \'%" + str(u) + "%\' AND NOT owner='" + str(household) + "'"
        mycursor.execute(sql)
    db.commit()


def update_game_date(title, last_played):
    """Record when a game was last played.

    Parameters
    ----------
    title : str
        the game's title
    last_played : datetime.datetime
    """
    db = choose_database("datadb")
    mycursor = db.cursor()
    sql = "UPDATE games SET last_played='" + str(last_played) + "' WHERE title='" + str(title) + "'"
    mycursor.execute(sql)
    db.commit()


def update_settings(table, who, to_set, to_unset):
    """Update settings for a user or group.

    Parameters
    ----------
    table : str
        typically 'settings' or 'group_settings'
    who : str
        typically username or a group's title
    to_set : list
        list of columns to set to 1
    to_unset : list
        list of columns to set to 0
    """
    db = choose_database("datadb")
    mycursor = db.cursor()
    new_set = ''
    for s in to_set:
        add_to_new_set = str(s) + '=1,'
        new_set += add_to_new_set
    for s in to_unset:
        add_to_new_set = str(s) + '=0,'
        new_set += add_to_new_set
    new_set = new_set[:-1]  # remove last comma
    if table == "settings":
        entry = "user"
    elif table == "group_settings":
        entry = "id"
    sql = "UPDATE " + table + " SET " + new_set + " WHERE " + entry + "='" + str(who) + "'"
    mycursor.execute(sql)
    db.commit()


def check_user(user):
    """Find out whether the user ever authenticated.

    Parameters
    ----------
    user : str
        ChatID

    Returns
    -------
    Boolean
    """
    result_user = search_single_entry(choose_database("auth"), "users", "id", user)

    if len(result_user) == 0:
        return 0
    else:
        return 1


def check_household(user):
    """Find out whether this user lives with others.

    Parameters
    ----------
    user : str
        username

    Returns
    -------
    str
        either only the user's name (if they live alone) or all names seperated by ' '
    """
    users_string = search_single_entry_substring(choose_database("datadb"), "households", "user_ids", user)

    if len(users_string) == 0:
        return user
    else:
        return users_string[0][0]


# TODO: db is set WITHIN the function.
def check_notify(table, who, column):
    """Find out whether to notify a user or group about a certain event.

    Parameters
    ----------
    table : str
        typically 'settings' or 'group_settings'
    who : str
        typically username or a group's title
    column : str
        type of event

    Returns
    -------
    -1  if no settings are found
     0  if the notification is unwished-for
     1  if the notification should be sent
    """
    if table == "settings":
        entry = 'user'
    elif table == "group_settings":
        entry = 'id'
    result = search_column_with_constraint(choose_database("datadb"), table, column, entry, who)

    if len(result) == 0:  # if user hasn't talked to bot yet, no settings
        return -1
    return result[0][0]
