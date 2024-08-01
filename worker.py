from threading import Event, Lock, Thread
import time

import redis

from redis_service import RedisService


WORKER_SLEEP_TIME = 10  # How long without users requests before going to bed.


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
        print(f"{int(time.time())} - {last_request_time} = {awake_time}")

        if awake_time > WORKER_SLEEP_TIME:
            Worker._stop_event.set()

    @staticmethod
    def main():
        while not Worker._stop_event.is_set():
            try:
                Worker._check_request_activity()
                print(Worker._stop_event.is_set())

            except redis.exceptions.ConnectionError as e:
                reconnected = False
                while not Worker._stop_event.is_set() and not reconnected:
                    reconnected = RedisService.try_reconnection()
                    Worker._stop_event.wait(5)

            except Exception as e:
                print(e)

            Worker._stop_event.wait(10)

        Worker._stop_event.clear()
