from starlette.datastructures import UploadFile
import os
from datetime import datetime

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def generate_filename(extension: str = "jpg"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{timestamp}.{extension}"


async def upload_image(file: UploadFile) -> str:
    contents = await file.read()
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = generate_filename(ext)
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    return file_path

async def upload_video(file: UploadFile) -> str:
    contents = await file.read()
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = generate_filename(ext)
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    return file_path
