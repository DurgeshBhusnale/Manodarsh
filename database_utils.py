import mysql.connector
import time
import base64
import datetime

def create_database():
    try:
        with mysql.connector.connect(
            host="localhost",
            user="Durgesh",
            password="durgesh#123",
            database="emotion_database"
        ) as mydb:
            mycursor = mydb.cursor()

            mycursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL
                )
            ''')

            mycursor.execute('''
                CREATE TABLE IF NOT EXISTS emotion_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    score FLOAT,
                    date DATE,  -- Added date column
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            mycursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_averages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    date DATE,
                    average_score FLOAT,
                    representative_image MEDIUMBLOB,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')


            mydb.commit()
            print("Database and tables created/checked successfully")
    except mysql.connector.Error as err:
        if err.errno == 1045:  # Incorrect username/password
            print("Incorrect username or password")
        elif err.errno == 1049:  # Unknown database
            print("Database does not exist")
        else:
            print(f"Something went wrong: {err}")

def add_user(name, image_base64):
    try:
        with mysql.connector.connect(
            host="localhost",
            user="Durgesh",
            password="durgesh#123",
            database="emotion_database"
        ) as mydb:
            mycursor = mydb.cursor()
            sql = "INSERT INTO users (name, user_image) VALUES (%s, %s)"  # Include user_image
            image_bytes = base64.b64decode(image_base64) #Decode image
            val = (name, image_bytes)
            mycursor.execute(sql, val)
            mydb.commit()
            print(f"User '{name}' added successfully.")
    except mysql.connector.IntegrityError:  # Handle duplicate user names
        print(f"User '{name}' already exists.")
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")

def get_user_id_from_name(name):
    try:
        with mysql.connector.connect(
            host="localhost",
            user="Durgesh",
            password="durgesh#123",
            database="emotion_database"
        ) as mydb:
            mycursor = mydb.cursor()
            sql = "SELECT id FROM users WHERE name = %s"
            val = (name,)
            mycursor.execute(sql, val)
            result = mycursor.fetchone()
            if result:
                return result[0]
            else:
                return None
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
        return None

def get_soldier_data():  # This function was missing!
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            mycursor.execute("SELECT id, name FROM users")  # Get user id and name
            soldiers = mycursor.fetchall()
            return soldiers
    except mysql.connector.Error as err:
        print(f"Error getting soldier data: {err}")
        return None


def store_emotion_data(user_id, score, date):  # No image here
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
        mydb.rollback()
        return False

def end_day(date, representative_images): # Receive representative images here
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

            # 2. Store representative images:
            for user_id, image_base64 in representative_images.items():
                image_bytes = base64.b64decode(image_base64)
                sql = """
                UPDATE daily_averages
                SET representative_image = %s
                WHERE user_id = %s AND date = %s;
                """
                val = (image_bytes, user_id, date)
                mycursor.execute(sql, val)

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

def connect_db():  # Context manager for db connection
    return mysql.connector.connect(
        host="localhost",
        user="Durgesh",
        password="durgesh#123",
        database="emotion_database"
    )