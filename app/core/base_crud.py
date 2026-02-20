from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager

from ..config.setting import Settings


class BaseCRUD:
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

    # 异步数据库会话管理
    @asynccontextmanager
    async def get_db(self):
        async with self.async_session as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
