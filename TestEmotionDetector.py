import cv2
import numpy as np
from keras.models import model_from_json
from collections import deque
import time

emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}
emotion_mapping = {  # Define emotion mapping to scores
    "Angry": 1, "Disgusted": 1, "Fearful": 1, "Happy": -1,
    "Neutral": 0, "Sad": 1, "Surprised": 1
}

# Load model (same as before)
json_file = open('model/emotion_model.json', 'r')
loaded_model_json = json_file.read()
json_file.close()
emotion_model = model_from_json(loaded_model_json)
emotion_model.load_weights("model/emotion_model.h5")
print("Loaded model from disk")

cap = cv2.VideoCapture(0)
time_window = deque(maxlen=60)  # 1-minute time window (adjust as needed)
last_score_calculation = time.time()
score_calculation_interval = 5  # Calculate score every 5 seconds

def calculate_depression_score(emotions):
    if not emotions:
        return 0
    total_score = sum(emotion_mapping[emotion] for emotion in emotions)
    average_score = total_score / len(emotions)
    return average_score


while True:
    ret, frame = cap.read()
    frame = cv2.resize(frame, (1280, 720))  # Resize for better visualization
    if not ret:
        break
    face_detector = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    num_faces = face_detector.detectMultiScale(gray_frame, scaleFactor=1.3, minNeighbors=5)

    for (x, y, w, h) in num_faces:
        cv2.rectangle(frame, (x, y - 50), (x + w, y + h + 10), (0, 255, 0), 4)
        roi_gray_frame = gray_frame[y:y + h, x:x + w]
        cropped_img = np.expand_dims(np.expand_dims(cv2.resize(roi_gray_frame, (48, 48)), -1), 0)
        emotion_prediction = emotion_model.predict(cropped_img)
        maxindex = int(np.argmax(emotion_prediction))
        predicted_emotion = emotion_dict[maxindex]  # Get emotion label
        cv2.putText(frame, predicted_emotion, (x + 5, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

        time_window.append(predicted_emotion)  # Add detected emotion to the time window

    # Calculate and display depression score periodically
    if time.time() - last_score_calculation >= score_calculation_interval:
        depression_score = calculate_depression_score(time_window)
        print(f"Depression Score: {depression_score:.2f}")  # Print with 2 decimal places
        last_score_calculation = time.time()
        cv2.putText(frame, f"Depression Score: {depression_score:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

    cv2.imshow('Emotion Detection', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()