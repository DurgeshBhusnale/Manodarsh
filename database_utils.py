import mysql.connector
import time

def create_database():
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="Durgesh",  # Your MySQL username
            password="durgesh#123",  
            database="emotion_database"
        )
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
                score FLOAT,  -- Use FLOAT for decimal scores
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
    finally:
        if mydb.is_connected():
            mydb.close()

def add_user(name):
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="Durgesh",  # Your MySQL username
            password="durgesh#123",  
            database="emotion_database"
        )
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
    finally:
        if mydb.is_connected():
            mydb.close()


def store_emotion_data(user_id, score):
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="Durgesh",  # Your MySQL username
            password="durgesh#123",  
            database="emotion_database"
        )
        mycursor = mydb.cursor()
        sql = "INSERT INTO emotion_data (user_id, score) VALUES (%s, %s)"
        val = (user_id, score)
        mycursor.execute(sql, val)
        mydb.commit()
    except mysql.connector.Error as err:
        print(f"Something went wrong: {err}")
    finally:
        if mydb.is_connected():
            mydb.close()

# Example usage (you'll likely call this part separately):
# create_database()  # Call this once to create the database and tables
# add_user("Alice")
# add_user("Bob")