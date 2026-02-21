from fastapi import APIRouter

from .user.controller import user_router
from .auth.controller import auth_router
from .task.controller import task_router
sys_router = APIRouter(prefix="/system")

sys_router.include_router(user_router)
sys_router.include_router(auth_router)
sys_router.include_router(task_router)




