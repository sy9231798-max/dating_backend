from typing import Any, Optional
from unittest import case
import json

from socketio import AsyncServer
from sqlalchemy.testing.pickleable import User
from sqlmodel import Session, select

from src.user.models import UserModel


class ChatHandler:
    def __init__(self, sio: AsyncServer):
        self.sio = sio
        self.connected_users = {}

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

    async def handle_message(self, data: str):
        data = json.loads(data)
        receiver = data["to"]
        if receiver not in self.connected_users:
            return

        message_type = data["type"]
        match message_type:
            case "makeCall":
                await self.sio.emit("makeCall", data, to=self.connected_users[receiver])
                return
            case "newMessage":
                await self.sio.emit("newMessage", data, to=self.connected_users[receiver])
                return
            case "typingIndictor":
                await self.sio.emit("typingIndictor", to=self.connected_users[receiver])

        if receiver in self.connected_users:
            await self.sio.emit(type, data)

    async def user_disconnected(self, sid: Any,db: Session):

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
