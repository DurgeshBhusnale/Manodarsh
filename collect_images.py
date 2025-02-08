import cv2
import os
import time

def collect_images(num_people, num_images_per_pose=15):
    """Collects images for multiple people with automated poses."""

    data_dir = "face_data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

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

    for i in range(num_people):
        person_name = input(f"Enter the name of person {i+1}: ")
        person_dir = os.path.join(data_dir, person_name)

        if not os.path.exists(person_dir):
            os.makedirs(person_dir)

        cap = cv2.VideoCapture(0)

        for pose in poses:
            image_count = 0
            while image_count < num_images_per_pose:
                ret, frame = cap.read()
                if not ret:
                    break

                cv2.putText(frame, pose, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.imshow("Collecting Images", frame)  # Show the frame *before* capturing

                key = cv2.waitKey(1)

                if key == ord('q'):  # quit completely
                    cap.release()
                    cv2.destroyAllWindows()
                    return  # Exit the function

                if key == ord('s'):  # Start capturing images for the current pose
                    time.sleep(2)  # Give user time to get into position
                    while image_count < num_images_per_pose:
                        ret, frame = cap.read()
                        if not ret:
                            break

                        cv2.imshow("Collecting Images", frame)  # Refresh the display *during* capture
                        image_filename = os.path.join(person_dir, f"{person_name}_{pose.replace(' ', '_')}_{image_count}.jpg")
                        cv2.imwrite(image_filename, frame)
                        print(f"Image saved: {image_filename}")
                        image_count += 1
                        time.sleep(0.5)  # Small delay

        cap.release()  # Release the camera *after* all poses are done for the person
        cv2.destroyAllWindows()
        print(f"Image collection complete for {person_name}.")


if __name__ == "__main__":
    num_people = int(input("Enter the number of people: "))
    collect_images(num_people)