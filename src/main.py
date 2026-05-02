import asyncio
from datetime import datetime
from typing import List, Optional, Type

import socketio
from fastapi import Depends
from graphql import GraphQLError
from sqlalchemy import event, desc
from sqlalchemy.orm import selectinload, Session
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from strawberry import Info

from src.graphql.graphql_handler import get_context, Query, graphql_app
from src.instance_handler import init_chat_handler
from src.api_config import api_router
from src.database import engine, get_session, settings
from sqlmodel import SQLModel

from jwt.exceptions import PyJWTError

from src.mongo_helper import message_collection
from src.token_helper import verify_token
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from PIL import Image
import os
import strawberry
from strawberry.fastapi import GraphQLRouter

from src.user.enums import Gender
from src.user.models import UserModel
from src.token_helper import create_token

fast_app = FastAPI()


@fast_app.on_event("startup")
def startup():
    SQLModel.metadata.create_all(engine)


#
# @event.listens_for(engine, "connect", insert=True)
# def set_search_path(dbapi_connection, connection_record):
#     cursor = dbapi_connection.cursor()
#     cursor.execute("SET SESSION search_path='app_schema, public'")
#     cursor.close()


fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





fast_app.include_router(graphql_app, prefix="/graphql")
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    ping_timeout=30,
    ping_interval=10
)

fast_app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
fast_app.include_router(api_router, prefix="/v1")
chatHandler = init_chat_handler(sio, message_collection)

print(settings.MONGODB_URL)


@sio.event
async def connect(sid, environ, auth):
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


BASE_DIR = "uploads"
CACHE_DIR = "cache"

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
SIZES = {
    "small": (150, 150),
    "medium": (600, 600),
    "large": (1200, 1200),
}


def get_paths(image_name: str, size: str):
    original_path = os.path.join(BASE_DIR, image_name)
    cached_path = os.path.join(CACHE_DIR, f"{size}_{image_name}")
    return original_path, cached_path


@fast_app.get("/image/{image_name}")
def serve_image(image_name: str, size: str = "medium"):
    if size not in SIZES and size != "original":
        raise HTTPException(status_code=400, detail="Invalid size")
    original_path, cached_path = get_paths(image_name, size)

    print(original_path, cached_path)
    if not os.path.exists(original_path):
        raise HTTPException(status_code=404, detail="Image not found")

    # Serve original directly
    if size == "original":
        return FileResponse(original_path)

    # If cached exists → return it
    if os.path.exists(cached_path):
        return FileResponse(cached_path)

    # Otherwise generate it
    image = Image.open(original_path)
    image = image.convert("RGB")

    image.thumbnail(SIZES[size])
    image.save(cached_path, optimize=True, quality=85)

    return FileResponse(cached_path)


@sio.on("agent_connect")
async def agent_connect(sid, data=None):
    db = next(get_session())
    await chatHandler.user_connected(sid, db=db)


@sio.on("user_connect")
async def user_connect(sid, data=None):
    if data is not None:
        db = next(get_session())
        await chatHandler.user_connected(sid, db=db)


@sio.on("message")
async def user_message(sid, data):
    print(f"Message received {data}")
    if data is not None:
        await chatHandler.handle_message(data, db=next(get_session()))


@sio.on("call")
async def user_calls(sid, data):
    if data is not None:
        await chatHandler.handle_call(sid=sid,data=data, db=next(get_session()))


@sio.event
async def disconnect(sid):
    db = next(get_session())
    await chatHandler.user_disconnected(sid, db=db)


@fast_app.get("/")
def root(db: Session = Depends(get_session)):
    return {"Helsslo": ""}


app = socketio.ASGIApp(sio, other_asgi_app=fast_app)


