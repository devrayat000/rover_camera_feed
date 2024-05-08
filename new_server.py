import os

os.environ["OPENCV_LOG_LEVEL"] = "SILENT"

import socketio.server
import asyncio
import uvicorn

# from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import cv2

# import base64

import camera_config

# create a Socket.IO server
sio = socketio.AsyncServer(
    logger=True,
    async_mode="asgi",
    cors_allowed_origins=[
        "http://localhost:1420",
        "http://192.168.0.101:1420",
        "http://192.168.0.102:1420",
        "http://192.168.0.105:1420",
        "http://10.18.121.97:1420",
        "http://172.17.80.1:1420",
        # "*",
    ],
)
app = socketio.ASGIApp(sio)


@sio.on(event="join_feed", namespace="/feed")
async def join_feed(sid, index: int):
    # print(f"join_feed: {index}")
    await sio.enter_room(sid, f"feed_receiver_{index}", namespace="/feed")


@sio.on(event="leave_feed", namespace="/feed")
async def leave_feed(sid, index):
    await sio.leave_room(sid, f"feed_receiver_{index}", namespace="/feed")


cams: "set[int]" = set()

camera_range = range(0, 3)
# capture = cv2.VideoCapture()


@sio.event(namespace="/feed")
async def connect(sid, environ, auth):
    await sio.emit(
        "camera_change",
        namespace="/feed",
        data=list(cams),
        skip_sid=True,
    )


@sio.event(namespace="/feed")
def disconnect(sid):
    pass


def get_transmit_permission(camera_index):
    if "/feed" not in sio.manager.rooms:
        return False

    feed_rooms = sio.manager.rooms["/feed"]
    if f"feed_receiver_{camera_index}" not in feed_rooms:
        return False

    return True


# TODO: Implement error transmitting
async def background_task(camera_index: int):
    print("background_task", camera_index)
    cap = cv2.VideoCapture(camera_index)
    # cap = capture
    # cap.open(camera_index)
    print(camera_index, cap)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # print("openned")
        if not get_transmit_permission(camera_index):
            await asyncio.sleep(0.0001)
            continue

        # print(f"camera_index: {camera_index}")

        frame = cv2.resize(frame, (400, 300))
        sus, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

        if not sus:
            continue

        # frame_data = base64.b64encode(buffer).decode("utf-8")
        start_time = time.time()

        await sio.emit(
            f"send_feed_{camera_index}",
            namespace="/feed",
            room=f"feed_receiver_{camera_index}",
            data=(buffer.tobytes(), start_time),
        )
        await asyncio.sleep(0.0001)

    print(f"camera_index: {camera_index} released")
    if camera_index in cams:
        cams.remove(camera_index)
    cap.release()
    # await asyncio.sleep(1)
    # await background_task(camera_index)


# async def get_free_camera_indices(current_indices: list[int]) -> list[int]:
#     print(current_indices)
#     indices = []
#     for idx in camera_range:
#         if idx not in current_indices:
#             print("trying", idx)
#             if capture.open(idx):
#                 print(f"idx {idx} is free")
#                 indices.append(idx)
#             capture.release()
#             await asyncio.sleep(0.1)

#     return indices


# async def watch_camera_change():
#     while True:
#         new_indices = await get_free_camera_indices(list(cams))
#         new_cams = set(new_indices)
#         diff = new_cams.difference(cams)

#         if len(diff) > 0:
#             print("added cams", diff)
#             for new_cam in diff:
#                 asyncio.create_task(background_task(new_cam))
#             cams.update(diff)
#             await sio.emit(
#                 "camera_change",
#                 namespace="/feed",
#                 data=list(cams),
#                 skip_sid=True,
#             )

#         print(list(cams), new_indices)
#         await asyncio.sleep(2)


ccc = [1, 2, 3]


async def look_for_camera_index():
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        print(
            "All available indices", camera_config.get_free_camera_indices(list(cams))
        )
        indices: "list[int]" = []
        for idx in camera_range:
            if idx not in list(cams):
                # print("Nnot in list", idx)
                # loop.create_task(background_task(idx))
                capture = cv2.VideoCapture(idx)
                # print("lspa", capture)
                if capture.isOpened():
                    print(f"index {idx} is free")
                    indices.append(idx)
                    # cams.add(idx)
                    print("looking for camera index", idx)
                capture.release()
            await asyncio.sleep(0.01)

        new_cams = set(indices)
        diff = new_cams.difference(cams)
        print("diff", diff)

        if len(diff) > 0:
            for new_cam in diff:
                loop.create_task(background_task(new_cam))
                # background_task(new_cam)
                # pass
            print("added cams", diff)
            cams.update(diff)
            await sio.emit(
                "camera_change",
                namespace="/feed",
                data=list(cams),
                skip_sid=True,
            )

        # print(list(cams), indices)
        print("total open cameras: ", cams)
        await asyncio.sleep(2)


async def run_server():
    # app.on_startup()
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info",
        # reload=True,
        loop="asyncio",
        workers=5,
        lifespan="on",
        # reload_includes=["*.py"],
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    # initial_indices = camera_config.get_camera_indices()
    # cams.update(initial_indices)
    # print(cams)
    await asyncio.gather(
        *[
            run_server(),
            # watch_camera_change(),
            look_for_camera_index(),
            # *[background_task(camera_index) for camera_index in [0, 1]],
        ]
    )


if __name__ == "__main__":
    asyncio.run(main())
