from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

# 显式加载环境变量文件
import os
env_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env")
load_dotenv(env_path)


class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8020
    API_WORKERS: int = 4
    DEBUG: bool = True

    ENVIRONMENT: str = "dev"

    # ================================================= #
    # ******************** 数据库配置 ******************* #
    # ================================================= #
    DATABASE_TYPE: Literal['mysql', 'postgres', 'sqlite', 'dm'] = "postgres"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5438
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "123456"
    DATABASE_NAME: str = "test_ai"

    # ================================================= #
    # ******************** 大模型配置 ******************* #
    # ================================================= #
    # OPENAI_BASE_URL: str
    # OPENAI_API_KEY: str
    # OPENAI_MODEL: str

    model_config = {
        "env_file": "../../config/.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # 忽略未定义的环境变量
    }

    @property
    def ASYNC_DB_URI(self) -> str:
        """获取异步数据库连接"""
        if self.DATABASE_TYPE == "mysql":
            return f"mysql+asyncmy://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}?charset=utf8mb4"
        elif self.DATABASE_TYPE == "postgres":
            return f"postgresql+asyncpg://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        elif self.DATABASE_TYPE == "sqlite":
            return f"sqlite+aiosqlite:///{self.DATABASE_NAME}.db"
        else:
            raise ValueError(f"数据库驱动不支持: {self.DATABASE_TYPE}, 异步数据库请选择 mysql、postgres、sqlite")

    @property
    def DB_URI(self) -> str:
        """获取同步数据库连接"""
        if self.DATABASE_TYPE == "mysql":
            return f"mysql+pymysql://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}?charset=utf8mb4"
        elif self.DATABASE_TYPE == "postgres":
            return f"postgresql+psycopg2://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        elif self.DATABASE_TYPE == "sqlite":
            return f"sqlite+pysqlite:///{self.DATABASE_NAME}.db"
        elif self.DATABASE_TYPE == "dm":
            return f"dm+dmPython://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        else:
            raise ValueError(f"数据库驱动不支持: {self.DATABASE_TYPE}, 同步数据库请选择 mysql、postgres、sqlite、dm")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
