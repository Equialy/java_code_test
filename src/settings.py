
import os
from os import path
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict



class Db(BaseModel):
    """
    Настройки для подключения к базе данных.
    """

    host: str
    port: int
    user: str
    password: str
    name: str
    scheme: str = 'public'

    provider: str = 'postgresql+asyncpg'

    @property
    def url_db(self) -> str:
        return f'{self.provider}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}'


class TestDb(BaseModel):
    """
    Настройки для подключения к тестовой базе данных.
    """

    test_host: str
    test_port: int
    test_user: str
    test_password: str
    test_name: str
    scheme: str = 'public'

    test_provider: str = 'postgresql+asyncpg'

    @property
    def url_db_test(self) -> str:
        return f'{self.test_provider}://{self.test_user}:{self.test_password}@{self.test_host}:{self.test_port}/{self.test_name}'




class Settings(BaseSettings):
    """
    Настройки модели.
    """
    debug: bool
    base_url: str


    cors_origins: list[str]
    test: int

    db: Db
    test_db: TestDb

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore',
    )


def get_settings():
    return Settings()

settings = get_settings()

SettingsService = Annotated[Settings, Depends(get_settings)]