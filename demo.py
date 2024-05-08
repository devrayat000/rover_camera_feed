import os

os.environ["OPENCV_LOG_LEVEL"] = "SILENT"

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

# capture = cv2.VideoCapture(0)

# while capture.isOpened():
#     print("Camera is opened")
# cp = cv2.VideoCapture()

# print(capture.isOpened())
# print(cp.open(1))
