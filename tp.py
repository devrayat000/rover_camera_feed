import socketio.server
import asyncio
import uvicorn
from concurrent.futures import ProcessPoolExecutor
import time
import cv2
import base64

import camera_config

cams = set()
camera_range = range(0, 3)
# capture = cv2.VideoCapture()

# create a Socket.IO server
sio = socketio.AsyncServer(
    # logger=True,
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


@sio.event(namespace="/feed")
async def connect(sid, environ, auth):
    pass


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


async def background_task(camera_index: int):
    cap = cv2.VideoCapture(camera_index)

    while cap.isOpened():
        # print(f"camera_index: {camera_index}")
        if not get_transmit_permission(camera_index):
            await asyncio.sleep(0.0001)
            continue

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (400, 300))
        sus, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 40])

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


def run_server(index: int):
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=5000 + index,
        log_level="info",
        # reload=True,
        loop="asyncio",
        workers=5,
        # reload_includes=["*.py"],
    )
    server = uvicorn.Server(config)

    tasks = asyncio.gather(
        *[
            server.serve(),
            background_task(index),
        ]
    )

    loop.run_until_complete(tasks)


async def main():
    with ProcessPoolExecutor(max_workers=5) as executor:
        while True:
            new_indices = camera_config.get_free_camera_indices(list(cams))
            new_cams = set(new_indices)
            diff = new_cams.difference(cams)

            if len(diff) > 0:
                print("added cams", diff)
                for new_cam in diff:
                    # asyncio.create_task(background_task(new_cam))
                    executor.submit(run_server, new_cam)
                cams.update(diff)
                # await sio.emit(
                #     "camera_change",
                #     namespace="/feed",
                #     data=list(cams),
                #     skip_sid=True,
                # )

            print(list(cams), new_indices)
            await asyncio.sleep(2)
        # for camera_index in camera_config.CAMERA_INDICES:
        #     executor.submit(run_server, camera_index)


if __name__ == "__main__":
    asyncio.run(main())
