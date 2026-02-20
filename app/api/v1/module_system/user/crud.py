from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import Any,Dict
from sqlalchemy import select
from fastapi import HTTPException


from app.config.setting import Settings
from ..user import User


class UserCRUD:

    def __init__(self,config: Settings):
        self.config = config
        #异步引擎
        self.engine = create_async_engine(
            config.ASYNC_DB_URI,
            echo=False,
            future=True,
        )


        #异步会话
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


    async def get_user_by_id(self,user_id:int) -> User|None:

        async with self.get_db() as db:

            user = await db.get(User, user_id)
            return user




    async def create_user(self, user: Dict[str, Any]) :
        try:
            async with self.get_db() as db:
                try:
                    new_user = User(**user)
                    db.add(new_user)
                    await db.commit()
                    return {
                        "success": True,
                        "message": "起号成功❤~"
                    }
                except Exception as e:

                    return EOFError(e)

        except Exception as e:

                return EOFError(e)


    async def check_username(self,username:str):
        async with self.get_db() as db:
            try:
                stmt = select(User).where(User.username == username)

                result = await db.execute(stmt)

                # 有重名用户
                if result.scalar_one_or_none() is not None:
                    return False
                else:
                    return True

            except Exception as e:
                raise e

    async def check_mobile(self,mobile:str):
        async with self.get_db() as db:
            try:
                stmt = select(User).where(User.mobile == mobile)

                result = await db.execute(stmt)

                # 有重名用户
                if result.scalar_one_or_none() is not None:
                    return  False
                else:
                    return True
            except Exception as e:
                # 处理其他异常
                from fastapi import HTTPException

                raise HTTPException(

                    status_code=500,

                    detail=f"检查用户名时发生错误: {str(e)}"

                )
