#
# from typing import AsyncGenerator
# from sqlalchemy.ext.asyncio import AsyncSession
# from fastapi import Request
# from redis.asyncio.client import Redis
#
#
#
# async def db_getter() -> AsyncGenerator[AsyncSession, None]:
#     """获取数据库会话连接
#
#     返回:
#     - AsyncSession: 数据库会话连接
#     """
#     async with async_db_session() as session:
#         async with session.begin():
#             yield session
#
#
# async def redis_getter(request: Request) -> Redis:
#     """获取Redis连接
#
#     参数:
#     - request (Request): 请求对象
#
#     返回:
#     - Redis: Redis连接
#     """
#     return request.app.state.redis