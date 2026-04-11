from typing import Any, Optional
import json

from motor.motor_asyncio import AsyncIOMotorCollection
from socketio import AsyncServer
from sqlmodel import Session, select
from src.user.models import UserModel, ConversationTable


class ChatHandler:
    def __init__(self, sio: AsyncServer,message_collection: AsyncIOMotorCollection):
        self.sio = sio
        self.connected_users = {}
        self.message_collection = message_collection

    async def user_connected(self, sid: Any, db: Session):
        session = await self.sio.get_session(sid)
        user = session.get("user")
        user_id = user["user_id"]

        print(f"{user_id} is online")
        db_user: Optional[UserModel] = db.exec(select(UserModel).where(UserModel.id == user_id)).first()
        if db_user is None:
            return

        db_user.is_active = True
        db.commit()
        self.connected_users[user_id] = sid
        await self.sio.emit("user_online", user_id)

    async def handle_message(self, data: str, db: Session):
        data = json.loads(data)
        receiver = data["to"]
        sender = data["from"]
        if receiver not in self.connected_users:
            return

        message_type = data["type"]
        match message_type:
            case "makeCall":
                await self.sio.emit("makeCall", data, to=self.connected_users[receiver])
                return
            case "newMessage":
                message_type = data["message_type"]
                await self.sio.emit("newMessage", data, to=self.connected_users[receiver])
                user_a = min(sender, receiver)
                user_b = max(sender, receiver)
                match message_type:
                    case "text":
                        last_message = data.get("message", "")
                    case "image":
                        last_message = "image"
                    case _:
                        last_message = "other"
                db_conversation = db.exec(select(
                    ConversationTable
                ).where(
                    ConversationTable.user_a_id == user_a, ConversationTable.user_a_id == user_b)
                ).one()

                if not db_conversation:
                    conversation = ConversationTable(
                        user_a_id=user_a,
                        user_b_id=user_b,
                        unread_count_a=0 if sender == user_a else 1,
                        unread_count_b=0 if sender == user_b else 1,
                        last_message=last_message
                    )
                    db.add(conversation)
                    db.commit()
                    return

                db_conversation.last_message = last_message
                if sender == user_a:
                    db_conversation.unread_count_b += 1
                else:
                    db_conversation.unread_count_a += 1

                db.commit()
                await self.message_collection.insert_one(data)
                return
            case "typingIndictor":
                await self.sio.emit("typingIndictor", data=sender, to=self.connected_users[receiver])

        if receiver in self.connected_users:
            await self.sio.emit(type, data)

    async def user_disconnected(self, sid: Any, db: Session):

        session = await self.sio.get_session(sid)
        user = session.get("user") if session else None
        user_id = user["user_id"]
        if user_id is None:
            for uid, s in self.connected_users.keys():
                if s == sid:
                    user_id = uid
                    break
        db_user: Optional[UserModel] = db.exec(select(UserModel).where(UserModel.id == user_id)).first()
        if db_user is None:
            return

        db_user.is_active = False
        db.commit()
        del self.connected_users[user_id]
        await self.sio.emit("user_offline", user_id)
        print(f"{user_id} is offline")
