from flask import Flask, render_template, request, jsonify, g
import sys
import os

# Get the parent directory (one level up)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the parent directory to sys.path
sys.path.insert(0, parent_dir)  # Insert at the beginning for highest priority

from database_utils import add_user, store_emotion_data, get_soldier_data, end_day, get_daily_averages, start_day, connect_db  # Absolute import

import datetime
import base64


app = Flask(__name__)

@app.route("/")
def index():
    soldiers = get_soldier_data()
    today = datetime.date.today()
    daily_averages = get_daily_averages(today)
    return render_template("index.html", soldiers=soldiers, daily_averages=daily_averages, today=today, base64=base64)

@app.route("/add_user", methods=["POST"])  # New route
def create_user():
    name = request.form.get("name")  # Get name from the form
    image_base64 = request.form.get("image")  # Get image from the form

    if add_user(name, image_base64):  # Pass image to add_user
        return jsonify({"message": "User created successfully"}), 200
    else:
        return jsonify({"message": "Error creating user"}), 500


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

@app.route("/end_day", methods=["POST"])
def close_day():
    date = datetime.date.today()
    representative_images = getattr(g, 'daily_images', {})  # Retrieve images from g

    if end_day(date, representative_images):  # Pass images to end_day
        # Clear images after use
        if hasattr(g, 'daily_images'):
            del g.daily_images
        return jsonify({"message": "Day ended successfully"}), 200
    else:
        return jsonify({"message": "Error ending day"}), 500

@app.route("/start_day", methods=["POST"])
def begin_day():
    date = datetime.date.today()
    if start_day(date):
        return jsonify({"message": "Day started successfully"}), 200
    else:
        return jsonify({"message": "Error starting day"}), 500

if __name__ == "__main__":
    app.run(debug=True)