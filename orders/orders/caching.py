from nameko import config
from cachetools import TTLCache
from functools import wraps
import hashlib  # We'll use hashlib to create cache keys
import redis
import json

# Create an in-memory cache with a max size and time-to-live (TTL)
cache_co = TTLCache(maxsize=500, ttl=600)  # cache for co: Create Order
cache_get = TTLCache(maxsize=500, ttl=600)  # cache for get: Get Order
cache_list = TTLCache(maxsize=500, ttl=600)  # cache for list: List Orders


def cache_get_order(func):
    @wraps(func)
    def wrapper(self, order_id):
        # Generate a cache key based on the method name and parameters
        cache_key = f"{func.__name__}:{order_id}"

        # Check if the result is in the cache
        cached_result = cache_get.get(cache_key)
        if cached_result is not None:
            return cached_result

        # If not in the cache, execute the method and store the result
        result = func(self, order_id)
        cache_get[cache_key] = result

        return result

    return wrapper


def cache_list_orders(func):
    @wraps(func)
    def wrapper(self):
        # Generate a cache key based on the method name and parameters
        cache_key = func.__name__

        # Check if the result is in the cache
        cached_result = cache_list.get(cache_key)
        if cached_result is not None:
            return cached_result

        # If not in the cache, execute the method and store the result
        result = func(self)
        cache_list[cache_key] = result

        return result

    return wrapper


def cache_create_order(func):
    @wraps(func)
    def wrapper(self, order_details):
        # Generate a cache key based on the method name and parameters
        cache_key = hashlib.md5(str(order_details).encode()).hexdigest()

        # Check if the result is in the cache
        cached_result = cache_co.get(cache_key)
        if cached_result is not None:
            return cached_result

        # If not in the cache, execute the method and store the result
        result = func(self, order_details)
        cache_co[cache_key] = result

        return result

    return wrapper


# Create a Redis connection
REDIS_URI_KEY = "REDIS_URI"
redis_client = redis.StrictRedis(decode_responses=True).from_url(
    config.get(REDIS_URI_KEY)
)


def cache_get_with_redis(func):
    @wraps(func)
    def wrapper(self, order_id):
        # Generate a cache key based on the method name and parameters
        cache_key = f"{func.__name__}:{order_id}"

        # Check if the result is in the Redis cache
        cached_result = redis_client.get(cache_key)
        if cached_result is not None:
            # If cached result exists, deserialize and return it
            return json.loads(cached_result)

        # If not in the cache, execute the method and store the result in Redis
        result = func(self, order_id)

        # Cache the result as a JSON string with an expiration time (e.g., 300 seconds)
        redis_client.setex(cache_key, 300, json.dumps(result))
        return result

    return wrapper


def cache_result_with_redis(cache_prefix, ttl):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Serialize the arguments to use as a cache key
            cache_key = (
                cache_prefix + hashlib.md5(json.dumps(args).encode()).hexdigest()
            )

            # Check if the result is in the Redis cache
            cached_result = redis_client.get(cache_key)
            if cached_result is not None:
                # If cached result exists, deserialize and return it
                return json.loads(cached_result)

            # If not in the cache, execute the method and store the result in Redis
            result = func(self, *args, **kwargs)
            # Cache the result as a JSON string with the specified TTL
            redis_client.setex(cache_key, ttl, json.dumps(result))

            return result

        return wrapper

    return decorator
