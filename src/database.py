from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel
from src.config import get_settings
from sqlalchemy import event

settings = get_settings()

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    echo=True,

)


def get_session():
    with Session(engine, autoflush=False, autocommit=False) as session:
        yield session
