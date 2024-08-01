from fastapi import FastAPI

from websockets.sync.client import connect


class WorkerService:
    @staticmethod
    def start():
        with connect("ws://localhost:8001/worker/start") as websocket:
            message = websocket.recv()
            return message

    @staticmethod
    def stop():
        with connect("ws://localhost:8001/worker/stop") as websocket:
            message = websocket.recv()
            return message

    @staticmethod
    def status():
        with connect("ws://localhost:8001/worker/status") as websocket:
            message = websocket.recv()
            return message


app = FastAPI()


@app.get("/weather/cities/{request_id}", tags=["weather"])
async def cities(request_id: int) -> dict:
    message = WorkerService.status()
    return {"message": message}


@app.post("/weather/cities/{request_id}", tags=["weather"])
async def cities(request_id: int) -> dict:
    # cities = redis.get()
    # if not cities or any([c.data > 10min for c in cities]):
    #     is_worker_off = redis.get('worker_status') == 'OFF'
    #     if is_worker_off:
    #         WorkerService.start_worker()
    #
    #     return len([c for c in cities if c.date < 10min]) / len(cities) * 100
    # return cities
    message = WorkerService.start()
    return {"message": message}


@app.get("/worker/start", tags=["worker"])
async def worker_start() -> dict:
    message = WorkerService.start()
    return {"message": message}


@app.get("/worker/stop", tags=["worker"])
async def worker_stop() -> dict:
    message = WorkerService.stop()
    return {"message": message}


@app.get("/worker/status", tags=["worker"])
async def worker_start() -> dict:
    message = WorkerService.status()
    return {"message": message}
