import json
import time
from fastapi import FastAPI, Request

from open_weather_service import CITIES_IDS
from redis_service import RedisService
from worker_service import WorkerService


RedisService.check_connection()
WorkerService.check_connection()


app = FastAPI()

EXCLUDED_PATHS_FROM_REQUEST_ACTIVITY = [
    '/favicon',
    '/worker/',
]

@app.get("/weather/cities", tags=["weather"])
async def cities() -> dict:
    def is_city_data_up_to_date(city) -> bool:
        TEN_MINUTES = 600  # How often OpenWeather refreshes their data from satellites and probes.
        return int(time.time()) - int(city.get('dt') or 0) < TEN_MINUTES

    cities_weather = RedisService.get('cities_weather')
    if not cities_weather:
        return {"message": 'No data available yet.'}

    cities_weather = json.loads(cities_weather)
    up_to_date_cities = [city for city in cities_weather if is_city_data_up_to_date(city)]
    if len(up_to_date_cities) == len(CITIES_IDS):
        return {"message": cities_weather}

    up_to_date_cities_percent = len(up_to_date_cities) / len(CITIES_IDS) * 100

    return {"message": f"Computing... {up_to_date_cities_percent:.2f}% ({len(up_to_date_cities)}/{len(CITIES_IDS)})"}


# These 3 are left for managing the worker thread, shouldn't go to production in a real environment.
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
        WorkerService.start()

    return response


RedisService.set('last_request_time', int(time.time()))  # Let 'now' be the last activity if the app has just boot up
WorkerService.start()
