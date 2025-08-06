# app/database/mongo.py

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.models.user import User
from app.models.document import AcceptedDocument
from app.models.rejected_document import RejectedDocument
from app.models.user import PasswordResetToken

client: AsyncIOMotorClient = None  # Will be initialized on startup

async def connect_to_mongo():
    global client
    client = AsyncIOMotorClient(settings.DB_URI)
    db = client[settings.DB_NAME]
    await init_beanie(
        database=db,
        document_models=[User, AcceptedDocument, RejectedDocument, PasswordResetToken],
    )

async def close_mongo_connection():
    client.close()

    