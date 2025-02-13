import mysql.connector
import base64
import datetime

# Database credentials (REPLACE THESE WITH YOUR ACTUAL CREDENTIALS)
DB_HOST = "localhost"
DB_USER = "Durgesh"
DB_PASSWORD = "durgesh#123"
DB_NAME = "emotion_database"

def connect_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def store_emotion_data(user_id, score, date):
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            sql = "INSERT INTO emotion_data (user_id, score, date) VALUES (%s, %s, %s)"
            val = (user_id, score, date)
            mycursor.execute(sql, val)
            mydb.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error storing data: {err}")
        mydb.rollback()  # Rollback on error
        return False

def get_soldier_data():
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            mycursor.execute("SELECT id, name FROM users")
            soldiers = mycursor.fetchall()
            return soldiers
    except mysql.connector.Error as err:
        print(f"Error getting soldier data: {err}")
        return None

def end_day(date):
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()

            # 1. Calculate daily averages:
            sql = """
            INSERT INTO daily_averages (user_id, date, average_score)
            SELECT user_id, date, AVG(score)
            FROM emotion_data
            WHERE date = %s
            GROUP BY user_id, date
            """
            mycursor.execute(sql, (date,))

            # 2. Get representative images (example: first image of the day):
            sql = """
            UPDATE daily_averages da
            JOIN (
                SELECT user_id, MIN(id) as min_id
                FROM emotion_data
                WHERE date = %s
                GROUP BY user_id
            ) as subq ON da.user_id = subq.user_id
            SET da.representative_image = (
                SELECT image FROM emotion_data
                WHERE id = subq.min_id
            )
            WHERE da.date = %s;
            """
            mycursor.execute(sql, (date, date)) #We are using the same table emotion_data to store images. if you have diffrent table then change it.

            mydb.commit()
            return True
    except mysql.connector.Error as err:
            print(f"Error ending day: {err}")
            mydb.rollback()
            return False

def get_daily_averages(date):
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            sql = "SELECT user_id, average_score, representative_image FROM daily_averages WHERE date = %s"
            mycursor.execute(sql, (date,))
            averages = mycursor.fetchall()
            return averages
    except mysql.connector.Error as err:
        print(f"Error getting daily averages: {err}")
        return None

def start_day(date):
    # For now, this just prints a message.  You might want to add logic here later.
    print(f"Starting day: {date}")
    return True  # Indicate success