"""
Centralized database connection management for AgentPress using Supabase.
"""

from typing import Optional
from supabase import create_async_client, AsyncClient
from utils.logger import logger
from utils.config import config

class DBConnection:
    """Singleton database connection manager using Supabase."""
    
    _instance: Optional['DBConnection'] = None
    _initialized = False
    _client: Optional[AsyncClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """No initialization needed in __init__ as it's handled in __new__"""
        pass

    async def initialize(self):
        """Initialize the database connection."""
        if self._initialized:
            return
                
        try:
            supabase_url = config.SUPABASE_URL
            # Use service role key preferentially for backend operations
            supabase_key = config.SUPABASE_SERVICE_ROLE_KEY or config.SUPABASE_ANON_KEY
            
            if not supabase_url or not supabase_key:
                logger.error("Missing required environment variables for Supabase connection")
                raise RuntimeError("SUPABASE_URL and a key (SERVICE_ROLE_KEY or ANON_KEY) environment variables must be set.")

            logger.debug("Initializing Supabase connection")
            self._client = await create_async_client(supabase_url, supabase_key)
            self._initialized = True
            key_type = "SERVICE_ROLE_KEY" if config.SUPABASE_SERVICE_ROLE_KEY else "ANON_KEY"
            logger.debug(f"Database connection initialized with Supabase using {key_type}")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise RuntimeError(f"Failed to initialize database connection: {str(e)}")

    @classmethod
    async def disconnect(cls):
        """Disconnect from the database."""
        if cls._client:
            logger.info("Disconnecting from Supabase database")
            await cls._client.close()
            cls._initialized = False
            logger.info("Database disconnected successfully")

    @property
    async def client(self) -> AsyncClient:
        """Get the Supabase client instance."""
        if not self._initialized:
            logger.debug("Supabase client not initialized, initializing now")
            await self.initialize()
        if not self._client:
            logger.error("Database client is None after initialization")
            raise RuntimeError("Database not initialized")
        return self._client

class SupabaseService:
    """Service for interacting with Supabase storage and database."""

    def __init__(self):
        self.db_connection = DBConnection()

    async def upload_file(self, bucket: str, path: str, file, content_type: str = None):
        """Upload a file to a Supabase storage bucket. Set content-type header if provided or if file is a PDF."""
        try:
            client = await self.db_connection.client
            file_options = {"upsert": "true"}
            # Set content-type if provided, or default to application/pdf for PDFs
            if content_type:
                file_options["content-type"] = content_type
            elif path.lower().endswith('.pdf'):
                file_options["content-type"] = "application/pdf"
            response = await client.storage.from_(bucket).upload(path, file, file_options=file_options)
            logger.debug(f"Upload response: {response}")
            if hasattr(response, 'error') and response.error:
                raise RuntimeError(f"Error uploading file: {response.error.message}")
            logger.info(f"File uploaded successfully to {bucket}/{path} with content-type {file_options.get('content-type')}")
        except Exception as e:
            logger.error(f"Failed to upload file to Supabase: {e}")
            raise

    async def insert_metadata(self, table: str, data_to_insert: dict): # Renamed 'metadata' param for clarity
        """Insert data into a Supabase table."""
        try:
            client = await self.db_connection.client
            response = await client.from_(table).insert(data_to_insert).execute()
            
            # More robust error checking
            if hasattr(response, 'error') and response.error:
                error_message = getattr(response.error, 'message', str(response.error))
                logger.error(f"Supabase insert error into table '{table}': {error_message}. Full error details: {response.error}")
                raise RuntimeError(f"Error inserting metadata into {table}: {error_message}")
            
            if not response.data:
                # This case might indicate an issue even if no explicit error (e.g., RLS preventing insert)
                # For a successful insert, we generally expect data (the inserted rows).
                logger.warning(f"Metadata insertion into {table} returned no data, though no explicit error was reported. Response: {response}")
                # Depending on strictness and specific table/RLS rules, this might warrant further investigation.

            logger.info(f"Data inserted successfully into {table}. Response data: {response.data}")
        except Exception as e:
            # Catching broader exceptions that might occur during the operation
            logger.error(f"Failed to insert metadata into Supabase table {table}: {e}", exc_info=True)
            raise


