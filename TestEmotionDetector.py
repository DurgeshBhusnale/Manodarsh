import cv2
import numpy as np
from keras.models import model_from_json
from collections import deque
import time
from database_utils import store_emotion_data, create_database, add_user, get_user_id_from_name
import pickle
import face_recognition
import base64
import requests
import datetime

emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}
emotion_mapping = {  # Define emotion mapping to scores (weighted)
    "Angry": 2, "Disgusted": 2, "Fearful": 2, "Happy": -1,
    "Neutral": 0, "Sad": 3, "Surprised": 1
}

# Load models
json_file = open('model/emotion_model.json', 'r')
loaded_model_json = json_file.read()
json_file.close()
emotion_model = model_from_json(loaded_model_json)
emotion_model.load_weights("model/emotion_model.h5")
print("Loaded emotion model from disk")

with open("face_recognition_model.pkl", "rb") as f:
    known_face_encodings, known_face_names = pickle.load(f)
print("Loaded face recognition model from disk")

cap = cv2.VideoCapture(1)
time_window = deque(maxlen=60)  # 1-minute time window
last_score_calculation = time.time()
score_calculation_interval = 5  # Calculate score every 5 seconds
data_points_to_store = []  # Accumulate data points for efficient database storage

create_database()  # Create the database and tables if they don't exist.

def get_recognized_name(frame):  # frame is roi_gray_frame (grayscale)
    frame_color = cv2.cvtColor(frame.copy(), cv2.COLOR_GRAY2BGR)  # Convert a COPY to color
    face_encodings = face_recognition.face_encodings(frame_color)  # Use the color copy
    if face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encodings[0])
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]
            return name
        else:
            return None
    else:
        return None

def calculate_depression_score(emotions):
    if not emotions:
        return 0

    total_score = 0
    for i, emotion in enumerate(emotions):
        weight = 0.9 ** (len(emotions) - 1 - i)  # Exponential decay
        total_score += emotion_mapping[emotion] * weight

    average_score = total_score / sum(0.9 ** (len(emotions) - 1 - i) for i in range(len(emotions)))  # Weighted Average
    return average_score


while True:
    ret, frame = cap.read()
    frame = cv2.resize(frame, (1280, 720))
    if not ret:
        break

    face_detector = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    num_faces = face_detector.detectMultiScale(gray_frame, scaleFactor=1.3, minNeighbors=5)

    user_id = None  # Initialize user_id outside the loop
    image_base64 = None # Initialize image_base64

    for (x, y, w, h) in num_faces:
        cv2.rectangle(frame, (x, y - 50), (x + w, y + h + 10), (0, 255, 0), 4)
        roi_gray_frame = gray_frame[y:y + h, x:x + w]
        cropped_img = np.expand_dims(np.expand_dims(cv2.resize(roi_gray_frame, (48, 48)), -1), 0)
        emotion_prediction = emotion_model.predict(cropped_img)
        maxindex = int(np.argmax(emotion_prediction))
        predicted_emotion = emotion_dict[maxindex]
        cv2.putText(frame, predicted_emotion, (x + 5, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

        recognized_name = get_recognized_name(roi_gray_frame)
        if recognized_name:
            user_id = get_user_id_from_name(recognized_name)
            if user_id:
                time_window.append(predicted_emotion)

                # Capture and encode image (only once per user per frame):
                ret, img_encoded = cv2.imencode('.jpg', roi_gray_frame) #Encode the image
                if ret:
                    image_base64 = base64.b64encode(img_encoded).decode('utf-8')

            else:
                print(f"User ID not found for {recognized_name}")
        else:
            print("No face recognized")

    # Calculate and display depression score periodically
    if time.time() - last_score_calculation >= score_calculation_interval:
        depression_score = calculate_depression_score(time_window)
        print(f"Depression Score: {depression_score:.2f}")

        if user_id is not None and image_base64 is not None:  # Check if user_id and image are available
            data = {
                "user_id": user_id,
                "score": depression_score,
                "date": str(datetime.date.today()),
                "image": image_base64  # Send encoded image
            }
            response = requests.post("http://127.0.0.1:5000/store_data", json=data) #Send data to the flask backend

            if response.status_code != 200:
                print(f"Error sending data to backend: {response.text}")

        cv2.putText(frame, f"Depression Score: {depression_score:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        last_score_calculation = time.time()

    cv2.imshow('Emotion Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()