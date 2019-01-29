def parse_single_db_entry(query_string):
    query_string = query_string.split('\'')[1]
    return query_string


def parse_csv(data_string):
    data_array = data_string.split(',')
    return data_array


def remove_first_csv(data_array):
    data_array = data_array.pop(0)
    return data_array


def csv_to_string(data_array):
    data_string = ','.join(data_array)
    return data_string


def remove_first_string(data_string):
    data_string = data_string.split(',', 1)[-1]
    return data_string


def parse_values_from_array(data_array):
    data_string = str(parse_csv(data_array))[1:-1]
    return data_string
