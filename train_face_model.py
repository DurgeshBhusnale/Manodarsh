import face_recognition
import os
import pickle
import argparse

def train_face_recognition_model(data_dir, model_filename="face_recognition_model.pkl"):
    known_face_encodings = []
    known_face_names = []

    for person_name in os.listdir(data_dir):
        person_dir = os.path.join(data_dir, person_name)
        if os.path.isdir(person_dir):
            for filename in os.listdir(person_dir):
                if filename.endswith((".jpg", ".png", ".jpeg")):
                    image_path = os.path.join(person_dir, filename)
                    image = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(image)
                    if face_encodings:  # Check if a face was detected
                        known_face_encodings.append(face_encodings[0])
                        known_face_names.append(person_name)

    with open(model_filename, "wb") as f:
        pickle.dump((known_face_encodings, known_face_names), f)

    print(f"Face recognition model trained and saved to {model_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train face recognition model.")
    parser.add_argument("--data_dir", default="face_data", help="Path to the face images directory.") # Add argument
    args = parser.parse_args()

    train_face_recognition_model(args.data_dir)  # Use argument