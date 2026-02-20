from fastapi import APIRouter,Request,Response,Depends

from app.api.v1.module_system.auth.service import AuthService
from app.config.setting import settings

from app.common.response import SuccessResponse,ErrorResponse
auth_router = APIRouter(prefix="/auth", tags=["认证授权"])

AuthService = AuthService()


@auth_router.post("/login")
async def login(
        request: Request,
        username : str|None = None,
        password : str|None = None,
):
    try:
        await AuthService.login(
            request,
            username = username,
            password = password,
            config= settings,
        )

        return SuccessResponse(
            msg= "登录成功",
        )

    except Exception as e:
        return ErrorResponse(
            msg= str(e),
        )