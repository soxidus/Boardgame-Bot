import mysql.connector


def setup_database():
        testdb = mysql.connector.connect(
            host="localhost",
            user="testuser",
            passwd="password",
            database="testdb"
        )

        cursor_testdb = testdb.cursor()
        cursor_testdb.execute("")

        authdb = mysql.connector.connect(
            host="localhost",
            user="testuser",
            passwd="password",
            database="auth"
        )

        cursor_authdb = authdb.cursor()
        cursor_authdb.execute("")

