from fastapi import APIRouter

v1Router = APIRouter(
    prefix="/v1",
)

from .Penetration.controller import penetrationRouter
from .tasks.controller import task_router

v1Router.include_router(penetrationRouter)
v1Router.include_router(task_router)