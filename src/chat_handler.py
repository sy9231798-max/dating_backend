import datetime
from enum import Enum
from typing import Any, Optional, clear_overloads
import json

from motor.motor_asyncio import AsyncIOMotorCollection
from socketio import AsyncServer
from sqlalchemy import func
from sqlmodel import Session, select

from src.user.model_wrapper import ConversationDataResponse, MessageResponse
from src.user.models import UserModel, ConversationTable


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

    # MessageBody()
    # {
    #     "to": 1,
    #     "from": 2,
    #     "type": MessageType.NEW_MESSAGE,
    #     "message_type": MessageContentType.Text,
    #     "message": "Hello World"
    # }

    async def handle_message(self, data: str, db: Session):
        data = json.loads(data)
        receiver = data["receiver"]
        sender = data["sender"]
        print(receiver in self.connected_users)

        print(self.connected_users.keys())
        if receiver not in self.connected_users:
            return

        message_type = data["type"]

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

                    await self.sio.emit("newConversation", ConversationDataResponse.conversation(receiver,
                                                                                                 conversation=conversation).model_dump_json(),
                                        to=self.connected_users[receiver])

                    print(f"CurrentConversation Sent To Sender {sender}")
                    await self.sio.emit("currentConversation", message.model_dump_json(),
                                        to=self.connected_users[sender])
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
                await self.sio.emit("newMessage", message.model_dump_json(), to=self.connected_users[receiver])
                await self.message_collection.insert_one(message.model_dump(exclude_none=True))
                return
            case "typingIndictor":
                await self.sio.emit("typingIndictor", data=sender, to=self.connected_users[receiver])

        if receiver in self.connected_users:
            await self.sio.emit(type, data)

    async def handle_call(self, data: str, db: Session):
        data = json.loads(data)
        call_type = data["type"]
        match call_type:
            case "makeCall":
                receiver = data["receiverId"]
                sender_details = data["callerDetail"]
                await self.sio.emit("callReceived",
                                    {
                                        "sdpOffer": data["sdpOffer"],
                                        "sender_details": sender_details,
                                    },
                                    to=self.connected_users[receiver]
                                    )
                return
            case "answerCall":
                caller_id = data["callerId"]
                await self.sio.emit("callAnswered", {
                    "sdpAnswer": data["sdpAnswer"],
                },
                                    to=self.connected_users[caller_id])
                return
            case "iceCandidate":
                ice_candidate = data["iceCandidate"]
                # await self.sio.emit("iceCandidate", {
                #     "from": "sender",
                #     "iceCandidate": ice_candidate,
                # }, to=self.connected_users[receiver])

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
        await self.sio.emit("user_offline", user_id)
        print(f"{user_id} is offline")
