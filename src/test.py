from database_functions import *

def main():
    parsed = parse_values_from_array()
    print(parsed)
    print(len(parsed))

    #add_household('a', 'b')

if __name__ == '__main__':
    main()