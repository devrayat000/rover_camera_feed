import socketio.server
import asyncio
import uvicorn
from concurrent.futures import ThreadPoolExecutor
import time
import cv2
import base64

# create a Socket.IO server
sio = socketio.AsyncServer(
    logger=True,
    async_mode="asgi",
    cors_allowed_origins=["http://localhost:1420"],
)
app = socketio.ASGIApp(sio)


@sio.on(event="send_feed", namespace="/feed")
async def send_feed(sid, data):
    await sio.emit(
        "receive_feed",
        data={
            **data,
            # "start_time": time.time(),
        },
        room="feed_receiver",
        namespace="/feed",
    )


class FeedData:
    def __init__(self, sid: str, index: int, cap: cv2.VideoCapture):
        self.sid = sid
        self.index = index
        self.cap = cap


caps: list[FeedData] = []


@sio.on(event="receive_feed", namespace="/feed")
async def receive_feed(sid, data):
    print("sid", sid)
    index = int(data["index"])
    cap_filter = list(filter(lambda x: x.index == index, caps))

    if len(cap_filter) <= 0:
        cap = cv2.VideoCapture(0)
        caps.append(FeedData(sid, index, cap))
    else:
        cap = cap_filter[0].cap

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        sus, buffer = cv2.imencode(".jpg", frame)

        if not sus:
            continue

        frame_data = base64.b64encode(buffer).decode("utf-8")
        start_time = time.time()

        await sio.emit(
            "send_feed",
            namespace="/feed",
            data={
                "frame_data": frame_data,
                "start_time": start_time,
            },
        )
        await asyncio.sleep(0.001)

    # await sio.enter_room(sid, "feed_receiver", namespace="/feed")


@sio.on(event="leave_feed", namespace="/feed")
async def leave_feed(sid, data):
    await sio.leave_room(sid, "feed_receiver", namespace="/feed")


@sio.event(namespace="/feed")
def connect(sid, environ, auth):
    pass


@sio.event(namespace="/feed")
def disconnect(sid):
    for data in caps:
        if data.sid == sid:
            data.cap.release()


async def main():
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=5000,
        log_level="info",
        reload=True,
        # loop=loop,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
