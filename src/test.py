from database_functions import *

def main():
    db = choose_database('testdb')
    mycursor = db.cursor()
    household = 'a b'
    mycursor.execute("INSERT INTO households (user_ids) VALUES (%s)", household)
    db.commit()


if __name__ == '__main__':
    main()