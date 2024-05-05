import cv2

index = 0
max_numbers_of_cameras_to_check = 10
while max_numbers_of_cameras_to_check > 0:
    capture = cv2.VideoCapture(index)
    if capture.read()[0]:
        print(index)
        capture.release()
    index += 1
    max_numbers_of_cameras_to_check -= 1
