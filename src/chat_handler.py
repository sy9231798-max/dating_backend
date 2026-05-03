import datetime
from enum import Enum
from typing import Any, Optional, clear_overloads, Type
import json

from motor.motor_asyncio import AsyncIOMotorCollection
from socketio import AsyncServer
from sqlalchemy.testing.pickleable import User
from sqlmodel import Session, select

from src.user.model_wrapper import ConversationDataResponse, MessageResponse
from src.user.models import UserModel, ConversationTable, CallHistory
from math import ceil
import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    NEW_MESSAGE = "newMessage"
    TYPING_INDICATOR = "typingIndicator"


class MessageContentType(str, Enum):
    Image = "image"
    Text = "text"


class ChatHandler:
    def __init__(self, sio: AsyncServer, message_collection: AsyncIOMotorCollection):
        self.sio = sio
        self.connected_users = {}
        self.message_collection = message_collection
        self.roomHandler = {}
        self.roomTimeHandler = {}

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
        receiver = data["receiver"]
        sender = data["sender"]
        print(receiver in self.connected_users)

        print(self.connected_users.keys())

        message_type = data["type"]

        print(f"{message_type}")
        match message_type:
            case "newMessage":
                message_type = data["message_type"]
                user_a = min(sender, receiver)
                user_b = max(sender, receiver)
                last_message = ""
                match message_type:
                    case "text":
                        last_message = data.get("message", "")
                    case "image":
                        last_message = "image"
                    case _:
                        last_message = "other"

                db_conversation = db.exec(select(ConversationTable).where(ConversationTable.user_a_id == user_a,
                                                                          ConversationTable.user_b_id == user_b)).first()

                print(f"Conversation {db_conversation is None}")
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
                    db.refresh(conversation)
                    message = MessageResponse(
                        conversation_id=conversation.id,
                        receiver=receiver,
                        sender=sender,
                        message_type=message_type,
                        message=data.get("message", ""),
                        send_at=datetime.datetime.now()
                    )
                    print(f"New Conversation Added To {receiver}")

                    if receiver in self.connected_users:
                        await self.sio.emit("newConversation",
                                            ConversationDataResponse.conversation(receiver,
                                                                                  conversation=conversation).model_dump_json(),
                                            to=self.connected_users[receiver])

                    print(f"CurrentConversation Sent To Sender {sender}")
                    await self.sio.emit("currentConversation",
                                        message.model_dump_json(),
                                        to=self.connected_users[sender]
                                        )
                else:
                    db_conversation.last_message = last_message
                    if sender == user_a:
                        db_conversation.unread_count_b += 1
                    else:
                        db_conversation.unread_count_a += 1
                    db.commit()

                    message = MessageResponse(
                        conversation_id=db_conversation.id,
                        receiver=receiver,
                        sender=sender,
                        message_type=message_type,
                        message=data.get("message", ""),
                        send_at=datetime.datetime.now()
                    )
                if receiver in self.connected_users:
                    await self.sio.emit("newMessage", message.model_dump_json(), to=self.connected_users[receiver])
                await self.message_collection.insert_one(message.model_dump(exclude_none=True))
                return
            case "typingIndictor":
                await self.sio.emit("typingIndictor", data=sender, to=self.connected_users[receiver])

        if receiver in self.connected_users:
            await self.sio.emit(type, data)

    async def handle_call(self, sid: Any, data: str, db: Session):
        data = json.loads(data)
        call_type = data["type"]
        logger.error(f"Data {data}")
        match call_type:
            case "makeCall":
                receiver = data["receiverId"]
                roomId = data["roomId"]
                sender_details = data["callerDetail"]
                session = await self.sio.get_session(sid)
                user = session.get("user") if session else None
                user_id = user["user_id"]
                if receiver in self.connected_users:
                    self.roomHandler[roomId] = (user_id, receiver)
                    self.roomTimeHandler[roomId] = datetime.datetime.now()
                    await self.sio.emit("callReceived",
                                        {
                                            "roomId": data["roomId"],
                                            "sender_details": sender_details,
                                        },
                                        to=self.connected_users[receiver]
                                        )

                await self.sio.emit("makeCallACK", to=self.connected_users[user_id])
                return
            case "callDrop":
                receiver = data["receiverId"]
                roomId = data["roomId"]
                if receiver in self.connected_users:
                    await self.sio.emit("callDrop",
                                        {
                                            "roomId": data["roomId"],
                                        },
                                        to=self.connected_users[receiver]
                                        )
                self.update_call_history(db, roomId)
                return
            case "rejectCall":
                room_id = data["roomId"]
                caller_id = data["callerId"]
                if caller_id in self.connected_users:
                    await self.sio.emit("rejectCall", to=self.connected_users[caller_id])
                self.update_call_history(db, room_id)
                return
            case "callDisconnect":
                roomId = data["roomId"]
                self.update_call_history(db, roomId)
            case "balanceDeduct":
                caller_id = data["caller_id"]
                db_user: Optional[UserModel] = db.query(UserModel).where(UserModel.id == caller_id).first()
                if db_user:
                    db_user.coins -= 10
                    db.commit()

    def update_call_history(self, db: Session, room_id: str):

        logger.error(f"Room Handler {self.roomHandler}")
        logger.error(f"Room Time Handler {self.roomTimeHandler}")
        if room_id in self.roomHandler:
            total_duration = datetime.datetime.now() - self.roomTimeHandler[room_id]
            db_room = db.query(CallHistory).where(CallHistory.room_id == room_id).first()
            if db_room:
                db_room.call_duration = ceil(total_duration.total_seconds())
                db.commit()
            del self.roomHandler[room_id]
            del self.roomTimeHandler[room_id]

    def find_key_by_user_id(self, user_id):
        for key, (uid, receiver) in self.roomHandler.items():
            if uid == user_id:
                return key
        return None

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
        if user_id in self.connected_users:
            del self.connected_users[user_id]

        roomId = self.find_key_by_user_id(user_id)
        if roomId is not None:
            self.update_call_history(db, roomId)

        await self.sio.emit("user_offline", user_id)
        print(f"{user_id} is offline")

    def available_for_call(self, receiver_id: int) -> tuple[bool, str]:

        if receiver_id not in self.connected_users:
            return False, "User is offline"

        for key, (uid, receiver) in self.roomHandler.items():
            if receiver == receiver_id:
                return False, "User is busy"

        return True, "Available"
