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

from src.api_config import api_router
from src.chat_handler import ChatHandler
from src.database import engine, get_session, settings
from sqlmodel import SQLModel, select

from jwt.exceptions import PyJWTError

from src.mongo_helper import message_collection
from src.token_helper import create_token, verify_token
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from PIL import Image
import os
import strawberry
from strawberry.fastapi import GraphQLRouter

from src.user.enums import Gender
from src.user.models import UserModel

fast_app = FastAPI()


@fast_app.on_event("startup")
def startup():
    SQLModel.metadata.create_all(engine)


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


@strawberry.type
class AdditionImageType:
    image_path: str
    created_at: datetime
    updated_at: datetime
    id: int
    user_id: int


@strawberry.type
class UserDataType:
    id: int
    first_name: str
    last_name: str
    phone_number: str
    email: str
    profile_picture: str
    video_picture: str
    dob: str
    gender: Gender
    hobby: List[str]
    state: str
    city: str
    lvl: int
    is_pending: Optional[bool]
    score: int
    created_at: datetime
    addition_images: List[AdditionImageType]
    is_active: bool


async def get_context(db: Session = Depends(get_session)):
    return {"db": db}


async def get_user_data_type(user: UserModel) -> UserDataType:
    return UserDataType(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone_number=user.phone_number,
        is_active=user.is_active,
        created_at=user.created_at,
        is_pending=True,
        video_picture=user.video_picture,
        dob=user.dob,
        lvl=user.lvl,
        hobby=user.hobby,
        profile_picture=user.profile_picture,
        addition_images=[AdditionImageType(
            created_at=images.created_at,
            image_path=images.image_path,
            updated_at=images.updated_at,
            user_id=images.user_id,
            id=images.id
        ) for images in user.addition_images],
        city=user.city,
        score=user.score,
        state=user.state,
        gender=user.gender
    )


@strawberry.type
class Query:
    @strawberry.field
    async def hello(self) -> str:
        return "Hello"

    @strawberry.field
    async def explore(self, info: Info) -> List[UserDataType]:
        db: Session = info.context["db"]
        # statement = (select(UserModel)
        #              .options(selectinload(UserModel.addition_images))
        #              .order_by(desc(UserModel.score)))
        # users: Optional[List[UserModel]] = db.exec(statement).all()
        users: Optional[List[Type[UserModel]]] = db.query(UserModel).options(
            selectinload(UserModel.addition_images)).order_by(desc(UserModel.score)).all()

        return [
            await get_user_data_type(user)
            for user in users
        ]

    @strawberry.field
    async def user_detail(self, info: Info, id: int) -> UserDataType:
        db: Session = info.context["db"]

        user: Optional[Type[UserModel]] = db.query(UserModel).where(UserModel.id == id).first()

        if user is None:
            raise GraphQLError(f"User with id {id} not found")
        return UserDataType(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone_number=user.phone_number,
            is_active=user.is_active,
            created_at=user.created_at,
            is_pending=True,
            video_picture=user.video_picture,
            dob=user.dob,
            lvl=user.lvl,
            hobby=user.hobby,
            profile_picture=user.profile_picture,
            addition_images=[AdditionImageType(
                created_at=images.created_at,
                image_path=images.image_path,
                updated_at=images.updated_at,
                user_id=images.user_id,
                id=images.id
            ) for images in user.addition_images],
            city=user.city,
            score=user.score,
            state=user.state,
            gender=user.gender
        )


schema = strawberry.Schema(Query)

graphql_app = GraphQLRouter(schema, context_getter=get_context)

fast_app.include_router(graphql_app, prefix="/graphql")
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    ping_timeout=30,
    ping_interval=10
)

fast_app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
fast_app.include_router(api_router, prefix="/v1")
chatHandler = ChatHandler(sio, message_collection)

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
        await chatHandler.handle_call(data, db=next(get_session()))


@sio.event
async def disconnect(sid):
    db = next(get_session())
    await chatHandler.user_disconnected(sid, db=db)


@fast_app.get("/")
def root(db: Session = Depends(get_session)):
    return {"Helsslo": ""}


app = socketio.ASGIApp(sio, other_asgi_app=fast_app)
