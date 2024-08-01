import redis

REDIS_HOST = 'localhost'
REDIS_PORT = 6379

class RedisService:
    redis_connection = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    @staticmethod
    def check_connection():
        try:
            RedisService.redis_connection.ping()
        except redis.exceptions.ConnectionError as e:
            raise ConnectionError(f"Error connecting to Redis. Is it running at '{REDIS_HOST}:{REDIS_PORT}'?.")

    @staticmethod
    def get(key):
        return RedisService.redis_connection.get(key)

    @staticmethod
    def set(key, value):
        return RedisService.redis_connection.set(key, value)

    @staticmethod
    def incrby(key, amount):
        return RedisService.redis_connection.incrby(key, amount)

    @staticmethod
    def ttl(key):
        return RedisService.redis_connection.ttl(key)

    @staticmethod
    def expire(key, seconds):
        return RedisService.redis_connection.expire(key, seconds)

    @staticmethod
    def try_reconnection():
        try:
            RedisService.redis_connection.ping()
            return True
        except redis.exceptions.ConnectionError as e:
            print(f"Reconnection to Redis Failed. Is it running at '{REDIS_HOST}:{REDIS_PORT}'?.")

        return False
