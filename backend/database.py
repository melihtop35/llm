"""
MongoDB Database Connection Module
Async MongoDB connection using Motor driver
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os

# MongoDB connection settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "llm_council")


class MongoDB:
    """MongoDB connection manager"""

    client: Optional[AsyncIOMotorClient] = None

    @classmethod
    async def connect(cls):
        """Connect to MongoDB"""
        if cls.client is None:
            cls.client = AsyncIOMotorClient(MONGODB_URL)
            # Test connection
            try:
                await cls.client.admin.command("ping")
                print(f"✅ Connected to MongoDB: {MONGODB_URL}")
            except Exception as e:
                print(f"⚠️ MongoDB connection failed: {e}")
                print("📁 Falling back to JSON file storage")
                cls.client = None

    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB"""
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            print("🔌 Disconnected from MongoDB")

    @classmethod
    def get_database(cls):
        """Get database instance"""
        if cls.client is None:
            return None
        return cls.client[DATABASE_NAME]

    @classmethod
    def get_collection(cls, name: str):
        """Get a collection from the database"""
        db = cls.get_database()
        if db is None:
            return None
        return db[name]

    @classmethod
    def is_connected(cls) -> bool:
        """Check if connected to MongoDB"""
        return cls.client is not None


# Collection names
CONVERSATIONS_COLLECTION = "conversations"
ANALYTICS_COLLECTION = "analytics"
SETTINGS_COLLECTION = "settings"


async def get_conversations_collection():
    """Get conversations collection"""
    return MongoDB.get_collection(CONVERSATIONS_COLLECTION)


async def get_analytics_collection():
    """Get analytics collection"""
    return MongoDB.get_collection(ANALYTICS_COLLECTION)


async def get_settings_collection():
    """Get settings collection"""
    return MongoDB.get_collection(SETTINGS_COLLECTION)
