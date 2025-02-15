import mysql.connector

try:
    mydb = mysql.connector.connect(
        host="localhost",
        user="Durgesh",
        password="durgesh#123",
        database="emotion_database"
    )
    print("Database connection successful!")
    mydb.close()
except mysql.connector.Error as err:
    print(f"Database connection error: {err}")