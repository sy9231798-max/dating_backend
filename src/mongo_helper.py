import certifi
from motor.motor_asyncio import AsyncIOMotorClient

from src.database import settings

client = AsyncIOMotorClient(settings.MONGODB_URL,
                            tlsCAFile=certifi.where()
                            )
database = client.chat_app  # Database Name
message_collection = database.get_collection("messages")

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

