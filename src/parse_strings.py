# coding=utf-8

import uuid


def parse_csv_to_array(data_string):
    """Parse one CSV string (delimited by commas) into an array."""
    data_array = data_string.split(',')
    return data_array


def parse_csv_import(data_string):
    """Parse CSV data into an array.

    Parameters
    ----------
    data_string : str
        entries should be delimited by \n, values by comma

    Returns
    -------
    data_array : list
        rows are taken from \n delimiters, columns from commas
    """
    data_array = data_string.split('\n')

    for _ in range(len(data_array)):
        data_array[_] = data_array[_].split(',')
        data_array[_] = list(filter(None, data_array[_]))

    return data_array


# TODO: rename to parse_array_to_csv
def array_to_csv(data_array):
    """Parse an array of data into a CSV.

    Parameters
    ----------
    data_array : list

    Returns
    -------
    data_string : str
        comma-delimited CSV string
    """
    data_string = ','.join(data_array)
    return data_string


def remove_first_string(query_string):
    """Remove the first entry of a comma-delimited string.

    Parameters
    ----------
    query_string : str
        looks something like "new_game,pseudouser,pseudotitle,..."

    Returns
    -------
    data_string : str
        looks something like "pseudouser,pseudotitle,..."
    """
    data_string = query_string.split(',', 1)[-1]
    return data_string


# TODO: Rename to parse_values_from_csv? or string?
def parse_values_from_query(query_string):
    """Parse query string into values for a database entry.

    Parameters
    ----------
    query_string : str
        looks something like "pseudouser,pseudotitle"

    Returns
    -------
    val_string : str
        looks something like "'pseudouser', 'pseudotitle'"
    """
    val_string = str(parse_csv_to_array(query_string))[1:-1]
    return val_string


# TODO: Rename to parse_...
def db_entries_to_messagestring(db_result):
    """Parses DB entries into a sorted list that can be used as message text.

    Parameters
    ----------
    db_result : list
        list of tuples

    Returns
    -------
    messagestring : str
        sorted list of all first column entries of db_result
    """
    messagestring = ""
    entries = []

    for _ in range(len(db_result)):
        entries.append(db_result[_][0])

    entries.sort()
    messagestring = ",\n".join(entries)
    return messagestring


#TODO: Rename to parse_...
def single_db_entry_to_string(db_entry):
    """Parse one DB entry into a string."""
    string = ""
    for _ in range(len(db_entry)):
        string += db_entry[_]
    return string


# TODO: Rename (specify usage for games, it generates values and not a query)
# only used for csv_import
def parse_game_values_from_array(data_sub_array, uuid=None):
    """Generate string of values for adding a game into the DB.

    Parameters
    ----------
    data_sub_array : list
        contains owner, title and playercount
    uuid : str or None
        if specified, should hold the game's UUID

    Returns
    -------
    val_string : str
        can be used as VALUES for DB import
    """
    # this could be done in fewer steps but to visualize the separate parts it's split here
    # !!ATTENTION!! if too much overhead is generated by initializing all those VARS refactor this!

    # use double quotes to escape quotes
    for _ in range(len(data_sub_array)):
        data_sub_array[_] = data_sub_array[_].replace("'", "''")
        data_sub_array[_] = data_sub_array[_].replace('"', '""')

    owner = '\'' + data_sub_array[0] + '\''
    title = '\'' + data_sub_array[1] + '\''
    players = '\'' + data_sub_array[2] + '\''
    if uuid:
        game_id = '\'' + uuid + '\''
    else:
        game_id = '\'' + generate_uuid_32() + '\''
    val_string = owner + "," + title + "," + players + "," + game_id

    return val_string


def generate_uuid_32():
    return uuid.uuid4().hex
