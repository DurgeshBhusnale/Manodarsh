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
                    name VARCHAR(255) UNIQUE NOT NULL,
                    soldier_id VARCHAR(255),  -- Added soldier_id
                    branch VARCHAR(255),      -- Added branch
                    captain_phone VARCHAR(255), -- Added captain_phone
                    wife_phone VARCHAR(255),    -- Added wife_phone
                    user_image VARCHAR(255)  -- Store the image PATH here
                )
            ''')

            mycursor.execute('''
                CREATE TABLE IF NOT EXISTS emotion_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    score FLOAT,
                    date DATE,
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
                    representative_image VARCHAR(255),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            mycursor.execute('''
                CREATE TABLE IF NOT EXISTS two_day_averages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    date DATE,
                    average_score FLOAT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            mydb.commit()
            print("Database and tables created/checked successfully")
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")  # Print the full MySQL error
        print(f"Error Number: {err.errno}")  # Print the error number
        print(f"SQL State: {err.sqlstate}") # Print SQL state
        if err.errno == 1045:  # Incorrect username/password
            print("Incorrect username or password")
        elif err.errno == 1049:  # Unknown database
            print("Database does not exist")
        else:
            print(f"Something went wrong: {err}")

def add_user(name, soldier_id, branch, captain_phone, wife_phone, image_path):
    try:
        with mysql.connector.connect(
            host="localhost",
            user="Durgesh",
            password="durgesh#123",
            database="emotion_database"
        ) as mydb:
            mycursor = mydb.cursor()
            sql = "INSERT INTO users (name, soldier_id, branch, captain_phone, wife_phone, user_image) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (name, soldier_id, branch, captain_phone, wife_phone, image_path) # Store image path
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
    
def get_user_phone_numbers(user_id):  # Plural: numbers
    """Retrieves both captain's and wife's phone numbers from the database."""
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            sql = "SELECT captain_phone, wife_phone FROM users WHERE id = %s"  # Get both columns
            val = (user_id,)
            mycursor.execute(sql, val)
            result = mycursor.fetchone()
            if result:
                captain_phone, wife_phone = result
                phone_numbers = []
                if captain_phone:
                    phone_numbers.append(captain_phone)
                if wife_phone:
                    phone_numbers.append(wife_phone)
                return phone_numbers  # Return the list
            else:
                return []  # No phone numbers found
    except mysql.connector.Error as err:
        print(f"Error getting user phone numbers: {err}")
        return []

# def get_soldier_data():  
#     try:
#         with connect_db() as mydb:
#             mycursor = mydb.cursor()
#             mycursor.execute("SELECT id, name FROM users")  # Get user id and name
#             soldiers = mycursor.fetchall()
#             return soldiers
#     except mysql.connector.Error as err:
#         print(f"Error getting soldier data: {err}")
#         return None


def store_emotion_data(user_id, score, date, timestamp):  # No image here
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            sql = "INSERT INTO emotion_data (user_id, score, date, timestamp) VALUES (%s, %s, %s, %s)"
            val = (user_id, score, date, timestamp)
            mycursor.execute(sql, val)
            mydb.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error storing data: {err}")
        mydb.rollback()
        return False

def end_day(date): # Receive representative images here
    try:
        with connect_db() as mydb:
            mydb.commit()
            return True
    except mysql.connector.Error as err:
        print(f"Error ending day: {err}")
        mydb.rollback()
        return False


def calculate_daily_averages(date):
    """Calculates the daily average emotion scores for all users."""
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            sql = """
                SELECT user_id, AVG(score)
                FROM emotion_data
                WHERE date = %s
                GROUP BY user_id
            """
            mycursor.execute(sql, (date,))
            averages = mycursor.fetchall()
            return averages
    except mysql.connector.Error as err:
        print(f"Error calculating daily averages: {err}")
        return None

def get_daily_averages(date):
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            sql = "SELECT user_id, average_score FROM daily_averages WHERE date = %s"
            mycursor.execute(sql, (date,))
            averages = mycursor.fetchall()
            return averages
    except mysql.connector.Error as err:
        print(f"Error getting daily averages: {err}")
        return None

def store_daily_average(user_id, date, average_score):
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            sql = """
                INSERT INTO daily_averages (user_id, date, average_score)
                VALUES (%s, %s, %s)
            """
            val = (user_id, date, average_score)
            mycursor.execute(sql, val)
            mydb.commit()
            return True
    except mysql.connector.Error as err:
        print(f"Error storing daily average: {err}")
        mydb.rollback()
        return False


def start_day(date):
    # For now, this just prints a message.  You might want to add logic here later.
    print(f"Starting day: {date}")
    return True  # Indicate success


def get_2_day_average(user_id, date):
    """Calculates the 2-day average emotion score for a user."""
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()

            # Calculate the date for yesterday
            yesterday = date - datetime.timedelta(days=1)

            # SQL query to get scores for today and yesterday from daily_averages
            sql = """
                SELECT AVG(average_score)
                FROM daily_averages
                WHERE user_id = %s AND date IN (%s, %s)
            """
            val = (user_id, date, yesterday)
            mycursor.execute(sql, val)
            result = mycursor.fetchone()

            if result and result[0] is not None:  # Check if a result was found
                return result[0]
            else:
                return None  # No data found for the user on those days

    except mysql.connector.Error as err:
        print(f"Error getting 2-day average: {err}")
        return None


def store_2_day_average(user_id, date, average_score):
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            sql = "INSERT INTO two_day_averages (user_id, date, average_score) VALUES (%s, %s, %s)"
            val = (user_id, date, average_score)
            mycursor.execute(sql, val)
            mydb.commit()
            return True
    except mysql.connector.Error as err:
        print(f"Error storing data: {err}")
        mydb.rollback()
        return False


def check_notification_needed(user_id, date, threshold=3.0):  # Default threshold
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            sql = "SELECT average_score FROM two_day_averages WHERE user_id = %s AND date = %s"
            val = (user_id, date)
            mycursor.execute(sql, val)
            result = mycursor.fetchone()

            if result and result[0] is not None:
                average_score = result[0]
                if average_score < threshold:
                    return True  # Notification needed
                else:
                    return False  # No notification needed
            else:
                return False  # No data found, no notification needed

    except mysql.connector.Error as err:
        print(f"Error checking notification: {err}")
        return False

def get_soldier_data_for_date(date):
    """Retrieves soldier data for a given date."""
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()

            # SQL query to get soldier data (corrected for 'id' column)
            sql = """
                SELECT
                    u.id,
                    u.name,
                    u.soldier_id,
                    u.wife_phone,
                    u.user_image,
                    da.average_score,
                    tda.average_score AS two_day_average
                FROM
                    users u
                INNER JOIN
                    daily_averages da ON u.id = da.user_id AND da.date = %s
                LEFT JOIN
                    two_day_averages tda ON u.id = tda.user_id AND tda.date = %s
            """
            val = (date, date)
            mycursor.execute(sql, val)
            results = mycursor.fetchall()

            soldier_data = []
            for row in results:
                user_id, name, soldier_id, wife_phone, user_image, avg_score, two_day_average = row
                soldier = {
                    "user_id": user_id,
                    "name": name,
                    "soldier_id": soldier_id,
                    "wife_phone": wife_phone,
                    "user_image": user_image,
                    "avg_score": avg_score,
                    "2day_avg": two_day_average,
                    "depression_risk": "High" if two_day_average is not None and two_day_average < 3.0 else "Low", #Assumed threshold of 3.0
                }
                soldier_data.append(soldier)

            return soldier_data
        
    except mysql.connector.Error as err:
        print(f"Error getting soldier data: {err}")
        return None


def connect_db():  # Context manager for db connection
    return mysql.connector.connect(
        host="localhost",
        user="Durgesh",
        password="durgesh#123",
        database="emotion_database"
    )