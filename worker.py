import json
import os
from threading import Event, Lock, Thread
import time

from dotenv import load_dotenv
import redis

from open_weather_service import CITIES_IDS, OpenWeatherService
from redis_service import RedisService


load_dotenv()

CITY_REFRESH_RATE = int(os.getenv('CITY_REFRESH_RATE'))  # How old an OpenWeather city data can be.
WORKER_SLEEP_TIME = int(os.getenv('WORKER_SLEEP_TIME'))  # How long without users requests before going to bed.
CITIES_FETCHED_PER_TICK = int(os.getenv('CITIES_FETCHED_PER_TICK') or 10)
TICK_TIME = int(os.getenv('TICK_TIME') or 10)

class Worker:
    """
    Worker class responsible for keeping the Redis cache up to date.
    This is a rather simplistic implementation for the task at hand. More robust dedicated
    libraries like Celery Beat are recommended for bigger projects.
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

            RedisService.set('last_request_time', int(time.time()))
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
    def _check_request_activity():
        """
        Checks if the web app hasn't received any requests in WORKER_SLEEP_TIME seconds and stops
        the worker activity if it is the case.
        """
        last_request_time = RedisService.get('last_request_time')
        if not last_request_time:
            return

        awake_time = int(time.time()) - int(last_request_time)

        if awake_time > WORKER_SLEEP_TIME:
            Worker._stop_event.set()
            print('Worker Thread: Going to bedge.')

    @staticmethod
    def _fetch_cities_data():
        def is_city_data_up_to_date(city):
            return int(time.time()) - int(city.get('dt') or 0) < CITY_REFRESH_RATE

        cached_data = RedisService.get('cities_weather')
        cached_data = json.loads(cached_data) if cached_data else list()
        cached_data = sorted(cached_data, key=lambda city: city.get('dt') or 0)  # Oldest at first
        cached_data_ids = [c.get('id') for c in cached_data]
        outdated_cities = [city.get('id') for city in cached_data if not is_city_data_up_to_date(city)]
        missing_cities = [city_id for city_id in CITIES_IDS if city_id not in cached_data_ids]
        cities_ids_to_update = [city_id for city_id in missing_cities + outdated_cities]

        # Fetch up to 10 cities every 10 seconds, not exceeding API call limits.
        api_budget = OpenWeatherService.get_api_budget()
        calls_count = min(CITIES_FETCHED_PER_TICK, api_budget)
        cities_ids_to_update = cities_ids_to_update[:calls_count]
        new_weather_data = OpenWeatherService.get_weather_for_cities(cities_ids_to_update)
        actual_calls_count = len(cities_ids_to_update)
        OpenWeatherService.update_api_budget(actual_calls_count)

        cached_data_dict = {
            city.get('id'): city
            for city in cached_data
        }
        [cached_data_dict.update({city.get('id'): city}) for city in new_weather_data]
        RedisService.set('cities_weather', json.dumps(list(cached_data_dict.values())))

    @staticmethod
    def main():
        print("Worker Thread: Waking up")
        while not Worker._stop_event.is_set():
            try:
                Worker._fetch_cities_data()
                Worker._check_request_activity()

            except redis.exceptions.ConnectionError as e:
                reconnected = False
                while not Worker._stop_event.is_set() and not reconnected:
                    reconnected = RedisService.try_reconnection()
                    Worker._stop_event.wait(5)

            except Exception as e:
                print(e)

            Worker._stop_event.wait(TICK_TIME)  # Fetch up to 10 cities every 10 seconds

        Worker._stop_event.clear()
