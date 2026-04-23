from datetime import datetime, timedelta

import jwt
import socketio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.openapi.utils import get_openapi
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import text, event
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from src.api_config import api_router
from src.chat_handler import ChatHandler
from src.database import engine, get_session, settings
from sqlmodel import SQLModel, Session, select
import src.models

from jwt.exceptions import PyJWTError

from src.mongo_helper import message_collection
from src.token_helper import create_token, verify_token

fast_app = FastAPI()


@event.listens_for(engine, "connect", insert=True)
def set_search_path(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET SESSION search_path='app_schema, public'")
    cursor.close()

SQLModel.metadata.create_all(engine)
fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    ping_timeout=30,
    ping_interval=10
)

fast_app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
fast_app.include_router(api_router, prefix="/v1")
chatHandler = ChatHandler(sio,message_collection)

print(settings.MONGODB_URL)

@sio.event
async def connect(sid, environ,auth):
    query_string = environ.get("QUERY_STRING", "")


    from urllib.parse import parse_qs
    params = parse_qs(query_string)
    token = params.get("token", [None])[0]
    if not token:
        return False
    try:
        payload = verify_token(token)
        await sio.save_session(sid, {"user": payload})
        print(f"Connected {sid} {payload}")
    except PyJWTError:
        return False


@sio.on("agent_connect")
async def agent_connect(sid, data=None):
    db = next(get_session())
    await chatHandler.user_connected(sid,db=db)


@sio.on("user_connect")
async def user_connect(sid, data=None):
    if data is not None:
        db = next(get_session())
        await chatHandler.user_connected(sid,db=db)


@sio.on("message")
async def user_message(sid, data):

    print(f"Message received {data}")
    if data is not None:
        await chatHandler.handle_message(data,db = next(get_session()))

@sio.on("call")
async def user_calls(sid, data):

    if data is not None:
        await chatHandler.handle_call(data,db = next(get_session()))


@sio.event
async def disconnect(sid):
    db = next(get_session())
    await chatHandler.user_disconnected(sid,db=db)



@fast_app.get("/")
def root(db: Session = Depends(get_session)):
    return {"Helsslo": ""}

app = socketio.ASGIApp(sio, other_asgi_app=fast_app)
