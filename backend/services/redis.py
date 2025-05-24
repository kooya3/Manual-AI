import redis.asyncio as redis
import os
from dotenv import load_dotenv
import asyncio
from utils.logger import logger
from typing import List, Any
from urllib.parse import urlparse, ParseResult

# Redis client
client = None
_initialized = False
_init_lock = asyncio.Lock()

# Constants
REDIS_KEY_TTL = 3600 * 24  # 24 hour TTL as safety mechanism
MAX_RETRIES = 5  # Increased Maximum number of connection retries
RETRY_DELAY = 2  # Increased Delay between retries in seconds


def initialize():
    """Initialize Redis connection using environment variables, prioritizing Upstash."""
    global client

    # Load environment variables if not already loaded
    load_dotenv()

    # Check for Upstash configuration first
    upstash_url = os.getenv('UPSTASH_REDIS_REST_URL')
    upstash_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')

    redis_url = None
    # redis_ssl is determined by the URL scheme, but keep for local fallback logic check
    redis_ssl = False

    if upstash_url and upstash_token:
        logger.info("Using Upstash Redis configuration")
        try:
            # Explicitly parse URL and construct it with extracted components
            parsed_url = urlparse(upstash_url)
            hostname = parsed_url.hostname
            port = parsed_url.port

            if hostname is None:
                logger.error(f"Upstash Redis URL '{upstash_url}' does not contain a valid hostname.")
            else:
                 # If port is None, use the default Redis SSL port (6379) as a fallback
                 if port is None:
                      logger.warning(f"Upstash Redis URL '{upstash_url}' does not contain an explicit port. Using default Redis SSL port 6379.")
                      port = 6379
                 # Use 'rediss' scheme for SSL (Upstash default), include token as password
                 # Construct the URL string explicitly with hostname and port
                 redis_url = f"rediss://:{upstash_token}@{hostname}:{port}"
                 logger.info(f"Constructed Redis URL for from_url (Upstash): {redis_url}")

        except Exception as e:
             logger.error(f"Failed to parse Upstash Redis URL or construct connection string: {e}", exc_info=True)
             # If parsing fails, redis_url remains None and falls through to local config

    # If Upstash config was not used or failed to parse, fallback to local Redis configuration
    if not redis_url:
        logger.info("Falling back to local Redis configuration")
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_password = os.getenv('REDIS_PASSWORD', '')
            # Convert string 'True'/'False' to boolean for local config
            redis_ssl_str = os.getenv('REDIS_SSL', 'False')
            redis_ssl = redis_ssl_str.lower() == 'true'

            # Construct URL for local config, use 'redis' or 'rediss' scheme based on redis_ssl
            scheme = 'rediss' if redis_ssl else 'redis'
            # Include password in the URL if present
            if redis_password:
                 redis_url = f"{scheme}://:{redis_password}@{redis_host}:{redis_port}"
            else:
                 redis_url = f"{scheme}://{redis_host}:{redis_port}"

            logger.info(f"Constructed local Redis URL for from_url: {redis_url}")

        except Exception as e:
             logger.error(f"Failed to construct local Redis connection string: {e}", exc_info=True)
             redis_url = None # Ensure redis_url is None if local config fails

    if not redis_url:
         logger.error("Redis URL could not be determined from environment variables.")
         client = None # Ensure client is None if configuration fails
         return client

    # Use from_url to create the client and handle connection pooling and SSL
    try:
        # Pass the constructed URL and any additional client kwargs
        # The from_url method handles parsing the URL and setting up the connection pool with SSL
        # We rely on the scheme (rediss:// or redis://) in the constructed URL for SSL
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=10.0,  # Increased timeout slightly
            socket_connect_timeout=10.0,  # Increased connect timeout slightly
            retry_on_timeout=True,
            health_check_interval=30,
            max_connections=200,  # Increased pool size for high concurrency
            # Removed explicit ssl=... parameter - relies on URL scheme
        )

        logger.info("Redis client created successfully using from_url (SSL inferred from scheme)")
        return client
    except Exception as e:
        logger.error(f"Failed to create Redis client using from_url: {e}", exc_info=True)
        client = None # Ensure client is None if client creation fails
        return client


async def initialize_async():
    """Initialize Redis connection asynchronously with retries."""
    global client, _initialized

    async with _init_lock:
        if not _initialized or client is None: # Double check if client is None
            logger.info("Initializing Redis connection asynchronously")
            # Call the synchronous initialize first to configure using from_url
            # This sets the global client variable
            initialize()

            # Check if client was successfully created by initialize()
            if client is None:
                 logger.error("Redis client not created by synchronous initialize. Cannot proceed with async ping.")
                 # Raise a specific error indicating initialization failure for the async part
                 raise ConnectionError("Redis client initialization failed at sync stage.")

            for attempt in range(MAX_RETRIES):
                try:
                    # Use client.ping() with a timeout
                    # This is an async operation and verifies the connection
                    await asyncio.wait_for(client.ping(), timeout=10.0) # Increased timeout for ping
                    logger.info("Successfully connected to Redis after async ping")
                    _initialized = True # Mark as initialized on successful ping
                    return client # Return the successfully connected client
                except (redis.ConnectionError, redis.TimeoutError, asyncio.TimeoutError, ConnectionError) as e:
                    # Catching ConnectionError from previous stage as well
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Failed to connect to Redis (attempt {attempt + 1}/{MAX_RETRIES}): {type(e).__name__} - {e}")
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        logger.error(f"Failed to connect to Redis after {MAX_RETRIES} attempts: {type(e).__name__} - {e}")
                        client = None # Ensure client is None on final failure
                        _initialized = False # Mark as not initialized on final failure
                        # Raise a clear error after all retries fail
                        raise ConnectionError(f"Failed to initialize Redis connection after {MAX_RETRIES} attempts") from e
                except Exception as e:
                     logger.error(f"An unexpected error occurred during Redis connection attempt {attempt + 1}/{MAX_RETRIES}: {type(e).__name__} - {e}", exc_info=True)
                     if attempt == MAX_RETRIES - 1:
                         client = None
                         _initialized = False
                         raise ConnectionError(f"Unexpected error during Redis initialization after {MAX_RETRIES} attempts") from e
                     await asyncio.sleep(RETRY_DELAY * (attempt + 1))

        # If already initialized and client is not None, just return the client
        if client is None:
            # This case might occur if initialize() failed but _initialized was somehow set to True prematurely.
            # It's a safeguard.
             logger.error("Redis client is None despite _initialized being True during async initialization.")
             raise ConnectionError("Redis client is not available after initialization attempt.")

    # If the lock was acquired and the client was already initialized, or initialization inside the lock succeeded
    if client is None:
         # Final check before returning
         logger.error("Redis client is None at the end of initialize_async.")
         raise ConnectionError("Redis client is not available after initialization process.")

    return client


async def close():
    """Close Redis connection."""
    global client, _initialized
    if client:
        logger.info("Closing Redis connection")
        try:
            # Use aclose for clients created with from_url as per redis-py docs
            await client.aclose()
        except Exception as e:
             logger.error(f"Error during Redis client close: {e}", exc_info=True)
        client = None
        _initialized = False
        logger.info("Redis connection closed")


async def close_connections():
    """Close all Redis connections in the pool."""
    global client
    if client:
        logger.info("Closing all Redis connections in pool")
        try:
            # For clients created with from_url, aclose closes the pool as well
            await client.aclose()
        except Exception as e:
            logger.error(f"Error during Redis pool close: {e}", exc_info=True)
        logger.info("Redis connections in pool closed")


async def get_client():
    """Get Redis client, initializing if needed with connection handling."""
    global client, _initialized, _init_lock

    # Check if client is already initialized and available
    if _initialized and client is not None:
        return client

    # If not initialized, acquire the lock and try initializing
    async with _init_lock:
        # Double-check inside the lock in case another coroutine initialized it while we were waiting
        if _initialized and client is not None:
            return client

        logger.info("Attempting to get or initialize Redis client (inside lock)")
        try:
            # Ensure async initialization is called to handle retries and setup
            # This function updates the global client and _initialized variables
            await initialize_async()
        except ConnectionError as e:
            logger.error(f"Failed to get or initialize Redis client: {e}")
            # Re-raise the connection error if initialization failed
            raise
        except Exception as e:
             logger.error(f"An unexpected error occurred during get_client initialization: {e}", exc_info=True)
             raise ConnectionError(f"Unexpected error during Redis client initialization: {e}") from e

    # After initialization attempt within the lock, check if client is available
    if client is None:
        # This should ideally not happen if initialize_async raises on failure, but as a safeguard
        logger.error("Redis client is None after attempted initialization inside lock.")
        raise ConnectionError("Redis client is not available after initialization attempt.")

    # Return the client if initialization was successful
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
            # Pass operation as a callable to execute it with the client
            if asyncio.iscoroutinefunction(operation):
                 return await operation(redis_client, *args, **kwargs)
            else:
                 return operation(redis_client, *args, **kwargs)
        except (redis.ConnectionError, redis.TimeoutError, ConnectionError) as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Redis operation failed after {MAX_RETRIES} attempts: {str(e)}")
                raise
            # Use a small delay between retries for operations
            await asyncio.sleep(RETRY_DELAY)
        except Exception as e:
             logger.error(f"An unexpected error occurred during Redis operation attempt {attempt + 1}/{MAX_RETRIES}: {type(e).__name__} - {e}", exc_info=True)
             if attempt == MAX_RETRIES - 1:
                 raise
             await asyncio.sleep(RETRY_DELAY)