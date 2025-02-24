from flask import Flask, redirect, render_template, request, jsonify, g, url_for, current_app
import sys
import os
import subprocess 

# Get the parent directory (one level up)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Add the parent directory to sys.path
sys.path.insert(0, parent_dir)  # Insert at the beginning for highest priority

from database_utils import add_user, store_emotion_data, get_soldier_data, end_day, get_daily_averages, start_day, connect_db, get_2_day_average,store_daily_average, store_2_day_average, check_notification_needed, get_user_phone_numbers, calculate_daily_averages  # Absolute import
from collect_images import collect_images
import datetime
import base64
from twilio.rest import Client
from config import IMAGE_DIR
import getpass

my_env = os.environ.copy()  # Create a copy of the current environment
my_env['PYTHONPATH'] = "D:\Emotion_detection_v2\.venv\Lib\site-packages"  # Or similar, depends on your system

app = Flask(__name__, static_folder='../static', static_url_path='/static')

# Global variable to store the process object
emotion_detector_process = None





def start_emotion_detector(date_str):
    """Starts the TestEmotionDetector.py script as a subprocess."""
    try:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        emotion_detector_path = os.path.join(root_dir, "TestEmotionDetector.py")

        venv_python = os.path.join("D:\Emotion_detection_v2\.venv\Scripts", "python.exe") # Path to python in venv bin directory
        # Start the subprocess (non-blocking)
        process = subprocess.Popen([venv_python, emotion_detector_path,date_str], cwd=root_dir, env=my_env)  # Set cwd and env
        print("Emotion detector started.")
        return process  # Return the process object

    except FileNotFoundError:
        print(f"Error: Emotion detector script not found at {emotion_detector_path}")
        return None
    except Exception as e:
        print(f"Error starting emotion detector: {e}")
        return None

def stop_emotion_detector(process):
    """Stops the TestEmotionDetector.py script."""
    if process:
        try:
            process.terminate()  # Or process.kill() for a more forceful stop
            process.wait()  # Wait for the process to fully terminate
            print("Emotion detector stopped.")
        except Exception as e:
            print(f"Error stopping emotion detector: {e}")
    else:
        print("No emotion detector process to stop.")


def send_sms_notification(user_id, date, average_score, threshold=3.0):
    phone_numbers = get_user_phone_numbers(user_id)  # Get the list of numbers

    if not phone_numbers:
        print(f"No phone numbers found for user {user_id}")
        return

    # Prepend +91 (assuming all numbers are Indian)
    message = f"Dear User {user_id},\n\nYour 2-day average emotion score for {date} is {average_score:.2f}, which is below the threshold of {threshold}."

    for phone_number in phone_numbers:  # Loop through the numbers
        #Prepend +91 (assuming all numbers are Indian)
        phone_number = "+91" + phone_number  # This is the change
        try:
            client = Client(account_sid, auth_token)  # Twilio client
            message = client.messages.create(
                to=phone_number,
                from_=from_phone_number,
                body=message
            )
            print(f"SMS notification sent to {phone_number} for user {user_id} on {date}")
        except Exception as e:
            print(f"Error sending SMS notification to {phone_number}: {e}") # Include the number in the error message


@app.route("/")
def index():
    today = datetime.date.today()
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            # Get the data from users table
            mycursor.execute("SELECT id, name, soldier_id, branch, captain_phone, wife_phone, user_image FROM users")
            soldiers = mycursor.fetchall()
            # Get the daily average
            mycursor.execute("SELECT user_id, average_score, representative_image FROM daily_averages WHERE date = %s", (today,))
            daily_averages = mycursor.fetchall()

        # Convert the data to a list of dictionaries (required by Jinja2):
        soldier_list = []
        for soldier in soldiers:
            soldier_list.append({
                "id": soldier[0],
                "name": soldier[1],
                "soldier_id": soldier[2],
                "branch": soldier[3],
                "captain_phone": soldier[4],
                "wife_phone": soldier[5],
                "user_image": soldier[6],
            })
        daily_average_list = []
        for avg in daily_averages:
            daily_average_list.append({
                "user_id": avg[0],
                "average_score": avg[1],
                "representative_image": avg[2],
            })

        return render_template("index.html", soldiers=soldier_list, daily_averages=daily_average_list, today=today, base64=base64)  # Pass the data to the template

    except Exception as e:
        print(f"Error fetching data: {e}")
        return render_template("index.html", error="Error fetching data") # Handle the error and still render the template (you might want a better error message)

@app.route("/add_soldier")  # Add this route
def add_soldier():
    return render_template("add_soldier.html")  # Serve the HTML file

@app.route("/add_user", methods=["POST"])
def create_user():
    name = request.form.get("name")
    soldier_id = request.form.get("soldier_id")
    branch = request.form.get("branch")
    captain_phone = request.form.get("captain_phone")
    wife_phone = request.form.get("wife_phone")
    image_path = collect_images(name) #Call collect_images

    if image_path: #Check if image collection was successful
        relative_image_path = os.path.relpath(image_path, IMAGE_DIR)  # Make path relative
        print(f"relative path is {relative_image_path}")
        if add_user(name, soldier_id, branch, captain_phone, wife_phone, relative_image_path):
            return redirect(url_for('add_soldier'))
            
        else:
            # return jsonify({"message": "Error creating user"}), 500
            return jsonify({""}), 500
    else:
        return jsonify({"message": "Image collection failed"}), 500


@app.route("/train_model", methods=["POST"])
def train_model():
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        print(f"Project Root: {project_root}")  # Print to the console
        current_app.logger.info(f"Project Root: {project_root}")
        
        train_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "train_face_model.py")) # Full path
        venv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".venv"))
        python_executable = os.path.join(venv_path, "Scripts", "python.exe") if os.name == "nt" else os.path.join(venv_path, "bin", "python")

        # Construct the command with the correct data_dir argument (relative to IMAGE_DIR)
        command = [python_executable, train_script_path, "--data_dir", ""]  # "face_data" is relative to IMAGE_DIR
        # Get the absolute path to the project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        process = subprocess.Popen(command,
                                   cwd=project_root,  # Run in the directory of app.py
                                   env=os.environ.copy(),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        stdout, stderr = process.communicate()

        if process.returncode == 0:
            return jsonify({"message": "Model training complete."}), 200
        else:
            error_message = stderr.decode("utf-8")
            current_app.logger.error(f"Model training failed: {error_message}")
            return jsonify({"message": f"Model training failed: {error_message}"}), 500

    except Exception as e:
        current_app.logger.error(f"Error starting model training: {e}")
        return jsonify({"message": f"Error starting model training: {e}"}), 500
    
@app.route("/store_data", methods=["POST"])
def store_data():
    data = request.get_json()
    user_id = data.get("user_id")
    score = data.get("score")
    form_date_str = request.form.get("date")  # Get date from form as string
    json_date_str = data.get("date")  # Get date from JSON as string
    image_base64 = data.get("image")
    timestamp = data.get("timestamp")

    if form_date_str:
        try:
            date = datetime.datetime.strptime(form_date_str, '%Y-%m-%d').date()  # Convert to date object
        except ValueError:
            return jsonify({"message": "Invalid date format in form. Please use %Y-%m-%d"}), 400
    elif json_date_str:
        try:
            date = datetime.datetime.strptime(json_date_str, '%Y-%m-%d').date()  # Convert to date object
        except ValueError:
            return jsonify({"message": "Invalid date format in JSON. Please use %Y-%m-%d"}), 400
    else:
        date = datetime.date.today()

    # Store image in g.daily_images (per request)
    if not hasattr(g, 'daily_images'):
        g.daily_images = {}
    g.daily_images.setdefault(user_id, image_base64)  # Store the first image for the user

    if store_emotion_data(user_id, score, date, timestamp):  # No image is stored here
        return jsonify({"message": "Data stored successfully"}), 200
    else:
        return jsonify({"message": "Error storing data"}), 500
            
@app.route("/end_day", methods=["POST"])
def close_day():
    global emotion_detector_process
    date_str = request.form.get("date")
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Please use %Y-%m-%d"}), 400

    # representative_images = getattr(g, 'daily_images', {})
    try:
        if end_day(date_obj):
            daily_averages = calculate_daily_averages(date_obj)  # Calculate daily averages

            if daily_averages:
                # Store daily averages
                for user_id, average_score in daily_averages:
                    store_daily_average(user_id, date_obj, average_score)

                # Check if there is data for the previous day
                previous_day = date_obj - datetime.timedelta(days=1)
                previous_day_averages = calculate_daily_averages(previous_day)

                if previous_day_averages: # only run if there is data for previous day.
                    for user_id, average_score in daily_averages:
                        two_day_average = get_2_day_average(user_id, date_obj)
                        if two_day_average is not None:
                            store_2_day_average(user_id, date_obj, two_day_average)
                            if check_notification_needed(user_id, date_obj):
                                send_sms_notification(user_id, date_obj, two_day_average)
                                print(f"Notification needed for user {user_id} on {date_obj}")

            stop_emotion_detector(emotion_detector_process)
            emotion_detector_process = None

            # if hasattr(g, 'daily_images'):
            #     del g.daily_images

            return jsonify({"message": "Day ended successfully"}), 200
        else:
            return jsonify({"message": "Error ending day"}), 500

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"message": "An unexpected error occurred."}), 500
        
@app.route("/start_day", methods=["POST"])
def begin_day():
    global emotion_detector_process
    date_str = request.form.get("date")  # Correct way to get date from form data

    if date_str is None or date_str == "":  # Check if date is missing or empty
        return jsonify({"message": "Date is required"}), 400  # Return error response

    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()  # Convert to date object

        if start_day(date_obj):  # Call your database function (if needed)
            emotion_detector_process = start_emotion_detector(date_str)  # Start the emotion detector
            return jsonify({"message": f"Starting day: {date_obj}"}), 200  # Success response
        else:
            return jsonify({"message": f"Error starting day: {date_obj}"}), 500  # Database error

    except ValueError:  # Handle invalid date format
        return jsonify({"message": "Invalid date format. Please use YYYY-MM-DD"}), 400  # Format error

    except Exception as e: # Catch any other exceptions
        print(f"An unexpected error occurred: {e}") # Print the error for debugging.
        return jsonify({"message": "An unexpected error occurred."}), 500 # Return a general error message to the client.


@app.route("/data_view")
def data_view():
    return render_template("soldier_data.html")

@app.route("/soldier_data")
def get_soldier_data():
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            mycursor.execute("SELECT id, name, soldier_id, branch, captain_phone, wife_phone, user_image FROM users") # Select all the columns you need.
            soldiers = mycursor.fetchall()

        soldier_list = []
        for soldier in soldiers:
            soldier_list.append({
                "id": soldier[0],
                "name": soldier[1],
                "soldier_id": soldier[2],
                "branch": soldier[3],
                "captain_phone": soldier[4],
                "wife_phone": soldier[5],
                "user_image": soldier[6],
                # Add other fields as needed
            })

        return jsonify(soldier_list)

    except Exception as e:
        print(f"Error fetching soldier data: {e}")
        return jsonify({"error": "Error fetching data"}), 500

@app.route("/depressed_soldiers_today")
def get_depressed_soldiers_today():
    today = datetime.date.today()  # Use date.today()
    try:
        with connect_db() as mydb:
            mycursor = mydb.cursor()
            mycursor.execute("SELECT user_id FROM daily_averages WHERE date = %s", (today,))
            depressed_user_ids = [row[0] for row in mycursor.fetchall()]

        depressed_soldiers = []
        seen_user_ids = set()  # Keep track of user IDs we've already processed

        for user_id in depressed_user_ids:
            if user_id not in seen_user_ids and check_notification_needed(user_id, today):  # Check if user_id is already in the set and check notification
                with connect_db() as mydb:
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT id, name, soldier_id, branch, captain_phone, wife_phone, user_image FROM users WHERE id = %s", (user_id,))
                    soldier = mycursor.fetchone()
                    if soldier:
                        depressed_soldiers.append({
                            "id": soldier[0],
                            "name": soldier[1],
                            "soldier_id": soldier[2],
                            "branch": soldier[3],
                            "captain_phone": soldier[4],
                            "wife_phone": soldier[5],
                            "user_image": soldier[6],
                        })
                        seen_user_ids.add(user_id)  # Add the user ID to the set

        return jsonify(depressed_soldiers)

    except Exception as e:
        print(f"Error fetching depressed soldiers data: {e}")
        return jsonify({"error": "Error fetching data"}), 500

if __name__ == "__main__":
    app.run(debug=True)