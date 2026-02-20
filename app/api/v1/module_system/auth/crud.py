from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.config.setting import Settings
from ..user import User

class CRUD:

    def __init__(self,config: Settings):
        self.config = config
        #异步引擎
        self.engine = create_async_engine(
            config.ASYNC_DB_URI,
            echo=False,
            future=True,
        )

        self.async_session = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )



    @asynccontextmanager
    async def get_db(self):
        async with  self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e


    async def get_pwd(self,username:str):
        async with self.get_db() as db:
            try:
                stmt = select(User.password).where(User.username == username)

                result = await db.execute(stmt)

                pwd = result.scalar_one_or_none()

                return pwd
            except Exception as e:
                raise e