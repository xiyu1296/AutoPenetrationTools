from fastapi import APIRouter

v1Router = APIRouter(
    prefix="/v1",
)

from .Penetration.controller import penetrationRouter

v1Router.include_router(penetrationRouter)