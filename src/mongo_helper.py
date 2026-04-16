from motor.motor_asyncio import AsyncIOMotorClient

from src.database import settings

client = AsyncIOMotorClient(settings.MONGODB_URL)
database = client.chat_app  # Database Name
message_collection = database.get_collection("messages")