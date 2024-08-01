

from threading import Event, Lock, Thread
from time import sleep
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


class OpenWeatherService:
    ...


class Worker:
    """
    Worker class responsible for keeping the Redis cache up to date.
    This is a rather simplistic implementation for the task at hand. More robust dedicated
    libraries like Celery are recommended for bigger projects.
    """
    _thread_instance: Thread = None
    _lock: Lock = Lock()
    _stop_event = Event()

    @staticmethod
    def _running() -> bool:
        return Worker._thread_instance is not None and Worker._thread_instance.is_alive()

    @staticmethod
    def running() -> bool:
        with Worker._lock:
            status: bool = Worker._running()

        return status

    @staticmethod
    def start() -> str:
        with Worker._lock:
            if Worker._running():
                return "ALREADY UP"

            Worker._thread_instance = Thread(target=Worker.main)
            Worker._thread_instance.start()
            return "UP"

    @staticmethod
    def stop():
        with Worker._lock:
            if not Worker._running():
                return "ALREADY DOWN"

            Worker._stop_event.set()
            Worker._thread_instance.join()
            Worker._stop_event.clear()
            return "DOWN" if not Worker._running() else "STILL UP"

    @staticmethod
    def main():
        while not Worker._stop_event.is_set():
            try:
                sleep(1)
            except Exception as e:
                ...


@app.websocket("/worker/start")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        status = Worker.start()
        await websocket.send_text(status)
    except WebSocketDisconnect as e:
        pass


@app.websocket("/worker/stop")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        status = Worker.stop()
        await websocket.send_text(status)
    except WebSocketDisconnect as e:
        pass


@app.websocket("/worker/status")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        status = 'UP' if Worker.running() else 'DOWN'
        await websocket.send_text(status)
    except WebSocketDisconnect as e:
        pass
