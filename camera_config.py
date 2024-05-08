import os

os.environ["OPENCV_LOG_LEVEL"] = "SILENT"

import cv2
import time
import asyncio

camera_range = range(0, 5)
capture = cv2.VideoCapture()


def get_camera_indices() -> list[int]:
    indices = []
    for index in camera_range:
        if capture.open(index):
            indices.append(index)
            capture.release()

    return indices


def get_free_camera_indices(current_indices: list[int]) -> list[int]:
    indices = []
    for index in camera_range:
        if index not in current_indices and capture.open(index):
            print(f"index {index} is free")
            # capture.release()
            indices.append(index)

    return indices


CAMERA_INDICES = [0, 1]
# cams = set()


# async def main():
#     while True:
#         new_indices = get_free_camera_indices(list(cams))
#         cams.update(new_indices)
#         print(list(cams), new_indices)
#         await asyncio.sleep(2)


# if __name__ == "__main__":
#     asyncio.run(main())
