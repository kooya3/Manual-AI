import redis.asyncio as redis
import os
from dotenv import load_dotenv
import asyncio
from utils.logger import logger
from typing import List, Any

# Redis client
client = None
_initialized = False
_init_lock = asyncio.Lock()

# Constants
REDIS_KEY_TTL = 3600 * 24  # 24 hour TTL as safety mechanism
MAX_RETRIES = 3  # Maximum number of connection retries
RETRY_DELAY = 1  # Delay between retries in seconds


def initialize():
    """Initialize Redis connection using environment variables."""
    global client

    # Load environment variables if not already loaded
    load_dotenv()

    # Get Redis configuration
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_password = os.getenv('REDIS_PASSWORD', '')
    # Convert string 'True'/'False' to boolean
    redis_ssl_str = os.getenv('REDIS_SSL', 'False')
    redis_ssl = redis_ssl_str.lower() == 'true'

    logger.info(f"Initializing Redis connection to {redis_host}:{redis_port}")

    # Create connection pool with optimized settings
    connection_pool_kwargs = dict(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=True,
        socket_timeout=5.0,  # Reduced timeout
        socket_connect_timeout=5.0,  # Reduced connect timeout
        retry_on_timeout=True,
        health_check_interval=30,
        max_connections=200,  # Increased pool size for high concurrency
        encoding='utf-8'
    )
    if redis_ssl:
        connection_pool_kwargs["connection_class"] = redis.SSLConnection

    connection_pool = redis.ConnectionPool(**connection_pool_kwargs)

    # Create Redis client using connection pool
    client = redis.Redis(
        connection_pool=connection_pool,
        retry_on_timeout=True,
        socket_keepalive=True
    )

    return client


async def initialize_async():
    """Initialize Redis connection asynchronously with retries."""
    global client, _initialized

    async with _init_lock:
        if not _initialized:
            logger.info("Initializing Redis connection")
            initialize()

            for attempt in range(MAX_RETRIES):
                try:
                    await client.ping()
                    logger.info("Successfully connected to Redis")
                    _initialized = True
                    return client
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Failed to connect to Redis (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                        await asyncio.sleep(RETRY_DELAY)
                    else:
                        logger.error(f"Failed to connect to Redis after {MAX_RETRIES} attempts: {e}")
                        client = None
                        raise

    return client


async def close():
    """Close Redis connection."""
    global client, _initialized
    if client:
        logger.info("Closing Redis connection")
        await client.aclose()
        client = None
        _initialized = False
        logger.info("Redis connection closed")


async def close_connections():
    """Close all Redis connections in the pool."""
    global client
    if client:
        await client.close()
        logger.info("Closed all Redis connections")


async def get_client():
    """Get Redis client, initializing if needed with connection handling."""
    global client, _initialized, _init_lock

    if not _initialized:
        async with _init_lock:
            if not _initialized:  # Double-check pattern
                client = initialize()
                _initialized = True

    if not client:
        raise ConnectionError("Failed to initialize Redis client")

    return client


# Basic Redis operations
async def set(key: str, value: str, ex: int = None):
    """Set a Redis key."""
    redis_client = await get_client()
    return await redis_client.set(key, value, ex=ex)


async def get(key: str, default: str = None):
    """Get a Redis key."""
    redis_client = await get_client()
    result = await redis_client.get(key)
    return result if result is not None else default


async def delete(key: str):
    """Delete a Redis key."""
    redis_client = await get_client()
    return await redis_client.delete(key)


async def publish(channel: str, message: str):
    """Publish a message to a Redis channel."""
    redis_client = await get_client()
    return await redis_client.publish(channel, message)


async def create_pubsub():
    """Create a Redis pubsub object."""
    redis_client = await get_client()
    return redis_client.pubsub()


# List operations
async def rpush(key: str, *values: Any):
    """Append one or more values to a list."""
    redis_client = await get_client()
    return await redis_client.rpush(key, *values)


async def lrange(key: str, start: int, end: int) -> List[str]:
    """Get a range of elements from a list."""
    redis_client = await get_client()
    return await redis_client.lrange(key, start, end)


async def llen(key: str) -> int:
    """Get the length of a list."""
    redis_client = await get_client()
    return await redis_client.llen(key)


# Key management
async def expire(key: str, time: int):
    """Set a key's time to live in seconds."""
    redis_client = await get_client()
    return await redis_client.expire(key, time)


async def keys(pattern: str) -> List[str]:
    """Get keys matching a pattern."""
    redis_client = await get_client()
    return await redis_client.keys(pattern)


async def execute_with_retry(operation, *args, **kwargs):
    """Execute Redis operation with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            redis_client = await get_client()
            return await operation(redis_client, *args, **kwargs)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Redis operation failed after {MAX_RETRIES} attempts: {str(e)}")
                raise
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        except Exception as e:
            logger.error(f"Unexpected Redis error: {str(e)}")
            raise