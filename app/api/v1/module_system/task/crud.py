from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import Any, Dict
from sqlalchemy import select
from fastapi import HTTPException

from app.config.setting import Settings
from ..user import User


# 这里是数据库操作层,我这里的初始化套用的之前的代码，用的异步引擎
class TaskCRUD:
    def __init__(self, config: Settings):
        self.config = config
        # 异步引擎
        self.engine = create_async_engine(
            config.ASYNC_DB_URI,
            echo=False,
            future=True,
        )

        # 异步会话
        self.async_session = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    def creat_task(self):
        """
            目前感觉你就可能只需要这里一个？
            把任务写入数据库
            用SQL alchemy orm！！！跟ai说下，orm！！！不要core风格！！！
            orm需要模型类，就是model里面定义的那个，跟ai说就行了
        """
        pass
