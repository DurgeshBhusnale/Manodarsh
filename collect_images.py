import cv2
import os
import time
from config import IMAGE_DIR

def collect_images(person_name, num_images_per_pose=15):
    """Collects images for a single person with automated poses."""
    
    person_dir = os.path.join(IMAGE_DIR, person_name)  # Use os.path.join() and IMAGE_DIR

    if not os.path.exists(person_dir):
        os.makedirs(person_dir)

    poses = [
        "Stand near to camera",
        "Tilt your face down",
        "Tilt your face to the right",
        "Tilt your face to the left",
        "Stand a little away",
        "Smile",
        "Frown",
        "Raise your eyebrows"
    ]

    cap = cv2.VideoCapture(1)  # Or 0, depending on your camera
    representative_image_path = None

    for pose in poses:
        image_count = 0
        while image_count < num_images_per_pose:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.putText(frame, pose, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.imshow("Collecting Images", frame)

            key = cv2.waitKey(1)

            if key == ord('q'):  # Quit completely
                cap.release()
                cv2.destroyAllWindows()
                return None  # Return None if the user quits

            if key == ord('s'):  # Start capturing images for the current pose
                time.sleep(2)  # Give user time to get into position
                while image_count < num_images_per_pose:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    cv2.imshow("Collecting Images", frame)
                    image_filename = os.path.join(person_dir, f"{person_name}_{pose.replace(' ', '_')}_{image_count}.jpg")  # Use os.path.join()
                    cv2.imwrite(image_filename, frame)
                    print(f"Image saved: {image_filename}")
                    if image_count == 0:  # Save the first image as representative
                        representative_image_path = image_filename
                    image_count += 1
                    time.sleep(0.3)  # Small delay

    cap.release()
    cv2.destroyAllWindows()
    print(f"Image collection complete for {person_name}.")
    return representative_image_path


if __name__ == "__main__":
    # This block should be empty or contain only very basic testing code.
    # The main logic should be in the function and called from another script.
    pass  # Or you could put a simple test call here, but keep it minimal.


