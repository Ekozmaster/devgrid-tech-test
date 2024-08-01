from websockets.sync.client import connect


WORKER_HOST = "localhost:8001"


class WorkerService:
    """
    Service class to communicate with our worker via websockets, avoiding HTTP overhead.
    """
    @staticmethod
    def start():
        with connect(f"ws://{WORKER_HOST}/worker/start") as websocket:
            message = websocket.recv()
            return message

    @staticmethod
    def stop():
        with connect(f"ws://{WORKER_HOST}/worker/stop") as websocket:
            message = websocket.recv()
            return message

    @staticmethod
    def status():
        with connect(f"ws://{WORKER_HOST}/worker/status") as websocket:
            message = websocket.recv()
            return message

    @staticmethod
    def check_connection():
        try:
            worker_status = WorkerService.status()
        except ConnectionRefusedError as e:
            raise ConnectionRefusedError(f"Error connecting to the Worker API. Is it running at '{WORKER_HOST}'?.")
