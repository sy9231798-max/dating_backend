from sqlalchemy import create_engine
from sqlmodel import Session

from src.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    echo=False,
)


def get_session():
    with Session(engine, autoflush=False, autocommit=False) as session:
        yield session
