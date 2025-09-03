# app/database/mongo.py

from beanie import init_beanie
import motor
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import logging
from app.core.config import settings
from app.models.user import User
from app.models.document import AcceptedDocument
from app.models.rejected_document import RejectedDocument
from app.models.user import PasswordResetToken

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient | None = None
db = None
_initialized = False

async def connect_to_mongo():
    global client, db, _initialized

    try:
        client = AsyncIOMotorClient(settings.DB_URI)
        db = client[settings.DB_NAME]

        # Test connection
        await client.admin.command('ping')
        logger.info(f"Connected to MongoDB: {settings.DB_NAME}")


        await init_beanie(
            database=db,
            document_models=[User, AcceptedDocument, RejectedDocument, PasswordResetToken],
        )

        _initialized = True
        logger.info("Beanie initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e


async def close_mongo_connection():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")


def get_database():
    """
    Synchronous MongoDB client (existing).
    """
    try:
        # FIXED: Use consistent settings reference
        sync_client = MongoClient(settings.DB_URI)  
        return sync_client[settings.DB_NAME]  # FIXED: Use consistent DB_NAME
    except Exception as e:
        logger.error(f"Failed to create a sync MongoDB client: {e}")
        raise


def get_database_async():
    """
    Async MongoDB client using Motor.
    Returns the database instance.
    """
    global client, db  # FIXED: Reference correct global variable 'db', not '_db'

    if client is None or db is None:
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.DB_URI)
        db = client[settings.DB_NAME]  # FIXED: Use 'db', not '_db'
        logger.info("Created new async MongoDB client.")

    return db  # FIXED: Return 'db', not '_db'

async def ensure_connection():
    """"Ensure MongoDB connection and Beanie initialization for Celery workers."""
    global _initialized

    if not _initialized:
        logger.info("Initializing MongoDB connection for Celery worker...")
        await connect_to_mongo()
    
    return db