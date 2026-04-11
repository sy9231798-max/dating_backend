import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PGDB_HOST: str
    PGDB_PORT: int
    PGDB_DB: str
    PGDB_USER: str
    PGDB_PASSWORD: str
    MONGODB_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow"
    )

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        # jdbc: postgresql: // localhost: 5432 / dummy
        return (
            f"postgresql://{self.PGDB_USER}:{self.PGDB_PASSWORD}"
            f"@{self.PGDB_HOST}:{self.PGDB_PORT}/{self.PGDB_DB}"
        )




@lru_cache()
def get_settings():
    return Settings()
