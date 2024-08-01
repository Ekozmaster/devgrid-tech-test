from functools import wraps
import time
from fastapi import FastAPI, Request

from redis_service import RedisService
from worker_service import WorkerService


RedisService.check_connection()
WorkerService.check_connection()


app = FastAPI()

EXCLUDED_PATHS_FROM_REQUEST_ACTIVITY = [
    '/favicon',
    '/worker/',
]

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


@app.middleware("http")
async def update_last_request_time(request: Request, call_next):
    response = await call_next(request)
    if not any([path in request.url.path for path in EXCLUDED_PATHS_FROM_REQUEST_ACTIVITY]):
        RedisService.set('last_request_time', int(time.time()))

    return response


RedisService.set('last_request_time', int(time.time()))  # Let 'now' be the last activity if the app has just boot up
