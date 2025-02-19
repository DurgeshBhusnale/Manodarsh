# import face_recognition
# import os
# import pickle
# import argparse
# from config import IMAGE_DIR  # Import IMAGE_DIR from config.py

# def train_face_recognition_model(data_dir, model_filename="face_recognition_model.pkl"):
#     known_face_encodings = []
#     known_face_names = []

#     full_data_dir = os.path.join(IMAGE_DIR, data_dir)  # Use IMAGE_DIR and passed in data_dir

#     if not os.path.exists(full_data_dir):  # Check if the directory exists
#         print(f"Error: Data directory not found: {full_data_dir}")
#         return  # Exit early if the directory doesn't exist

#     for person_name in os.listdir(full_data_dir):
#         person_dir = os.path.join(full_data_dir, person_name)
#         if os.path.isdir(person_dir):
#             for filename in os.listdir(person_dir):
#                 if filename.endswith((".jpg", ".png", ".jpeg")):
#                     image_path = os.path.join(person_dir, filename)
#                     image = face_recognition.load_image_file(image_path)
#                     face_encodings = face_recognition.face_encodings(image)
#                     if face_encodings:
#                         known_face_encodings.append(face_encodings[0])
#                         known_face_names.append(person_name)

#     model_filename = os.path.abspath(model_filename)  # Absolute path

#     with open(model_filename, "wb") as f:
#         pickle.dump((known_face_encodings, known_face_names), f)

#     print(f"Face recognition model trained and saved to {model_filename}")

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Train face recognition model.")
#     parser.add_argument("--data_dir", default="face_data", help="Path to the face images directory (relative to IMAGE_DIR).")  # Relative to IMAGE_DIR!
#     args = parser.parse_args()

#     train_face_recognition_model(args.data_dir)

import face_recognition
import os
import pickle
import argparse
from config import IMAGE_DIR
import logging  # Import the logging module

# Configure logging to a file in the project root
log_file = os.path.join(os.path.dirname(__file__), "training.log")  # Log file in project root
logging.basicConfig(filename=log_file, level=logging.DEBUG,  # Set logging level as needed
                    format='%(asctime)s - %(levelname)s - %(message)s')

def train_face_recognition_model(data_dir, model_filename="face_recognition_model.pkl"):
    known_face_encodings = []
    known_face_names = []

    if data_dir: # Check if data_dir is not empty
        full_data_dir = os.path.join(IMAGE_DIR, data_dir)
    else:
        full_data_dir = IMAGE_DIR # if data_dir is empty, then full_data_dir is just the IMAGE_DIR

    logging.info(f"Full Data Directory: {full_data_dir}")

    if not os.path.exists(full_data_dir):
        logging.error(f"Error: Data directory not found: {full_data_dir}")  # Log the error
        return  # Exit early

    for person_name in os.listdir(full_data_dir):
        person_dir = os.path.join(full_data_dir, person_name)
        if os.path.isdir(person_dir):
            for filename in os.listdir(person_dir):
                if filename.endswith((".jpg", ".png", ".jpeg")):
                    image_path = os.path.join(person_dir, filename)
                    try:  # Add a try-except block for image loading
                        image = face_recognition.load_image_file(image_path)
                        face_encodings = face_recognition.face_encodings(image)
                        if face_encodings:
                            known_face_encodings.append(face_encodings[0])
                            known_face_names.append(person_name)
                    except Exception as e:
                        logging.exception(f"Error loading image {image_path}: {e}")  # Log image loading errors

    model_filename = os.path.abspath(model_filename)
    logging.info(f"Model Filename (Absolute): {model_filename}")  # Log the absolute path

    try:  # Add a try-except block for file saving
        with open(model_filename, "wb") as f:
            pickle.dump((known_face_encodings, known_face_names), f)
        logging.info("Model saved successfully.")
    except Exception as e:
        logging.exception(f"Error saving model: {e}")  # Log file saving errors

    logging.info("Training completed.")  # Log completion

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train face recognition model.")
    parser.add_argument("--data_dir", default="face_data", help="Path to the face images directory (relative to IMAGE_DIR).")
    args = parser.parse_args()

    train_face_recognition_model(args.data_dir)