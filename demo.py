import cv2

index = 0
max_numbers_of_cameras_to_check = 10

INDICES = []

while max_numbers_of_cameras_to_check > 0:
    try:
        capture = cv2.VideoCapture(index)
        if capture.isOpened():
            INDICES.append(index)
            capture.release()
        index += 1
        max_numbers_of_cameras_to_check -= 1
    except:
        continue

print(INDICES)
