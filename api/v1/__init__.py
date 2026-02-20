from fastapi import APIRouter

v1Router = APIRouter(
    prefix="/v1",
)

from api.v1.Penetration.tasks.controller import penetrationRouter

v1Router.include_router(penetrationRouter)
