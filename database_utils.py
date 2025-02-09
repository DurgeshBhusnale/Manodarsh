import mysql.connector
import time

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
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

def add_user(name):
    try:
        with mysql.connector.connect(
            host="localhost",
            user="Durgesh",
            password="durgesh#123",
            database="emotion_database"
        ) as mydb:
            mycursor = mydb.cursor()
            sql = "INSERT INTO users (name) VALUES (%s)"
            val = (name,)
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

def store_emotion_data(data_points):  # data_points is a list of (user_id, score) tuples
    try:
        with mysql.connector.connect(
            host="localhost",
            user="Durgesh",
            password="durgesh#123",
            database="emotion_database"
        ) as mydb:
            mycursor = mydb.cursor()
            sql = "INSERT INTO emotion_data (user_id, score) VALUES (%s, %s)"
            mycursor.executemany(sql, data_points)  # Insert all in one go
            mydb.commit()
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")


# Example usage (you'll likely call this part separately):
# create_database()  # Call this once to create the database and tables
# add_user("Alice")
# add_user("Bob")