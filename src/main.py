from datetime import datetime, timedelta

import jwt
import socketio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.openapi.utils import get_openapi
from starlette import status
from starlette.middleware.cors import CORSMiddleware

from src.api_config import api_router
from src.chat_handler import ChatHandler
from src.database import engine, get_session
import src.models
from src.token_helper import create_token, verify_token

fast_app = FastAPI()

from sqlmodel import SQLModel, Session

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
fast_app.include_router(api_router, prefix="/v1")
chatHandler = ChatHandler(sio)


class JWTError:
    pass


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
    except JWTError:
        return False


@sio.on("agent_connect")
async def agent_connect(sid, data=None):

    if data is not None:
        db = next(get_session())
        await chatHandler.user_connected(sid,db=db)


@sio.on("user_connect")
async def user_connect(sid, data=None):
    if data is not None:
        db = next(get_session())
        await chatHandler.user_connected(sid,db=db)


@sio.on("message")
async def user_message(sid, data):
    if data is not None:
        await chatHandler.handle_message(data)


@sio.event
async def disconnect(sid):
    db = next(get_session())
    await chatHandler.user_disconnected(sid,db=db)


app = socketio.ASGIApp(sio, other_asgi_app=fast_app)
#
# from fastapi import FastAPI, File, UploadFile
# from pydantic import BaseModel
# import base64
# import os
# from datetime import datetime
#
# from starlette.requests import Request
#
# app = FastAPI()
#
#
#
#
# # ----------- Helper function -----------
# def generate_filename(extension: str = "jpg"):
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
#     return f"{timestamp}.{extension}"
#
#
# # ----------- Endpoint 1: Raw Image Upload -----------
# @app.post("/upload/raw")
# async def upload_raw(file: UploadFile = File(...)):
#     contents = await file.read()
#
#     # Get extension
#     ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
#     filename = generate_filename(ext)
#
#     file_path = os.path.join(UPLOAD_DIR, filename)
#
#     with open(file_path, "wb") as f:
#         f.write(contents)
#
#     return {
#         "message": "File uploaded successfully",
#         "filename": filename,
#         "path": file_path
#     }
#
#
# # ----------- Request Model for Base64 -----------
# class Base64Image(BaseModel):
#     image: str  # base64 string
#
#
# # ----------- Endpoint 2: Base64 Image Upload -----------
#
# @app.post("/upload/raw-body")
# async def upload_raw_body(request: Request):
#     body = await request.body()  # raw bytes
#
#     # Try to detect extension from headers
#     content_type = request.headers.get("content-type", "")
#
#     if "png" in content_type:
#         ext = "png"
#     elif "jpeg" in content_type or "jpg" in content_type:
#         ext = "jpg"
#     elif "webp" in content_type:
#         ext = "webp"
#     else:
#         ext = "jpg"  # fallback
#
#     filename = generate_filename(ext)
#     file_path = os.path.join(UPLOAD_DIR, filename)
#
#     with open(file_path, "wb") as f:
#         f.write(body)
#
#     return {
#         "message": "Raw body image saved",
#         "filename": filename,
#         "content_type": content_type,
#         "size_bytes": len(body)
#     }
#
#
# @app.post("/upload/base64")
# async def upload_base64(data: Base64Image):
#     try:
#         # Remove data URL prefix if present
#         if "base64," in data.image:
#             data.image = data.image.split("base64,")[1]
#
#         image_bytes = base64.b64decode(data.image)
#
#         filename = generate_filename("jpg")
#         file_path = os.path.join(UPLOAD_DIR, filename)
#
#         with open(file_path, "wb") as f:
#             f.write(image_bytes)
#
#         return {
#             "message": "Base64 image saved successfully",
#             "filename": filename,
#             "path": file_path
#         }
#
#     except Exception as e:
#         return {"error": str(e)}
