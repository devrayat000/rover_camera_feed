import socketio.server
import asyncio
import uvicorn
from concurrent.futures import ThreadPoolExecutor
import time
import cv2
import base64

import camera_config

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


class FeedData:
    def __init__(self, sid: str, index: int, cap: cv2.VideoCapture):
        self.sid = sid
        self.index = index
        self.cap = cap


@sio.on(event="join_feed", namespace="/feed")
async def join_feed(sid, index: int):
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
        if not get_transmit_permission(camera_index):
            await asyncio.sleep(0.0001)
            continue

        # print(f"camera_index: {camera_index}")
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (400, 300))
        sus, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])

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


async def main():
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info",
        # reload=True,
        loop="asyncio",
        workers=4,
    )
    server = uvicorn.Server(config)
    # await server.serve()

    await asyncio.gather(
        *[
            server.serve(),
            *[
                background_task(camera_index)
                for camera_index in camera_config.CAMERA_INDICES
            ],
        ]
    )


if __name__ == "__main__":
    asyncio.run(main())
