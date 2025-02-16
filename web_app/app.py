from flask import Flask, redirect, render_template, request, jsonify, g, url_for
import sys
import os
import subprocess 

# Get the parent directory (one level up)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the parent directory to sys.path
sys.path.insert(0, parent_dir)  # Insert at the beginning for highest priority

from database_utils import add_user, store_emotion_data, get_soldier_data, end_day, get_daily_averages, start_day, connect_db  # Absolute import
from collect_images import collect_images
import datetime
import base64

my_env = os.environ.copy()  # Create a copy of the current environment
my_env['PYTHONPATH'] = "D:\Emotion_detection_v2\.venv\Lib\site-packages"  # Or similar, depends on your system

app = Flask(__name__)

# Global variable to store the process object
emotion_detector_process = None

def start_emotion_detector():
    """Starts the TestEmotionDetector.py script as a subprocess."""
    try:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        emotion_detector_path = os.path.join(root_dir, "TestEmotionDetector.py")

        venv_python = os.path.join("D:\Emotion_detection_v2\.venv\Scripts", "python.exe") # Path to python in venv bin directory
        # Start the subprocess (non-blocking)
        process = subprocess.Popen([venv_python, emotion_detector_path], cwd=root_dir, env=my_env)  # Set cwd and env
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


@app.route("/")
def index():
    soldiers = get_soldier_data()
    today = datetime.date.today()
    daily_averages = get_daily_averages(today)
    return render_template("index.html", soldiers=soldiers, daily_averages=daily_averages, today=today, base64=base64)

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
        if add_user(name, soldier_id, branch, captain_phone, wife_phone, image_path):
            return redirect(url_for('add_soldier'))
            # return jsonify({"message": "User created successfully"}), 200
        else:
            return jsonify({"message": "Error creating user"}), 500
    else:
        return jsonify({"message": "Image collection failed"}), 500


@app.route("/train_model", methods=["POST"])
def train_model():
    try:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        data_dir = os.path.join(root_dir, "face_data")  # Absolute path to face_data
        print(os.getcwd())
        subprocess.Popen(["python", "../train_face_model.py", "--data_dir", data_dir], cwd=os.path.dirname(__file__), env=my_env)
        return jsonify({"message": "Model training started."}), 200
    except Exception as e:
        return jsonify({"message": f"Error starting model training: {e}"}), 500


@app.route("/store_data", methods=["POST"])
def store_data():
    data = request.get_json()
    user_id = data.get("user_id")
    score = data.get("score")
    date = data.get("date")
    image_base64 = data.get("image")

    # Store image in g.daily_images (per request)
    if not hasattr(g, 'daily_images'):
        g.daily_images = {}
    g.daily_images.setdefault(user_id, image_base64)  # Store the first image for the user

    if store_emotion_data(user_id, score, date):  # No image is stored here
        return jsonify({"message": "Data stored successfully"}), 200
    else:
        return jsonify({"message": "Error storing data"}), 500

@app.route("/end_day", methods=["POST"])  # Correct route name
def close_day():
    global emotion_detector_process
    date = datetime.date.today()
    representative_images = getattr(g, 'daily_images', {})

    if end_day(date, representative_images):
        stop_emotion_detector(emotion_detector_process)  # Stop detector
        emotion_detector_process = None  # Reset
        if hasattr(g, 'daily_images'):
            del g.daily_images
        return jsonify({"message": "Day ended successfully"}), 200
    else:
        return jsonify({"message": "Error ending day"}), 500

@app.route("/start_day", methods=["POST"])
def begin_day():
    global emotion_detector_process
    date_str = request.form.get("date")  # Correct way to get date from form data

    if date_str is None or date_str == "":  # Check if date is missing or empty
        return jsonify({"message": "Date is required"}), 400  # Return error response

    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()  # Convert to date object

        if start_day(date_obj):  # Call your database function (if needed)
            emotion_detector_process = start_emotion_detector()  # Start the emotion detector
            return jsonify({"message": f"Starting day: {date_obj}"}), 200  # Success response
        else:
            return jsonify({"message": f"Error starting day: {date_obj}"}), 500  # Database error

    except ValueError:  # Handle invalid date format
        return jsonify({"message": "Invalid date format. Please use YYYY-MM-DD"}), 400  # Format error

    except Exception as e: # Catch any other exceptions
        print(f"An unexpected error occurred: {e}") # Print the error for debugging.
        return jsonify({"message": "An unexpected error occurred."}), 500 # Return a general error message to the client.

if __name__ == "__main__":
    app.run(debug=True)