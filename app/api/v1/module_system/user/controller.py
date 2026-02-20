from fastapi import APIRouter
from pydantic import ValidationError


from app.config.setting import settings
from .service import UserService

from app.common.response import SuccessResponse,ErrorResponse

from .param import User
user_router = APIRouter(prefix="/User", tags=["用户管理"])
user_service = UserService(config=settings)


@user_router.post("/register")
async def register(username:str,password : str ,mobile : str , emile : str|None = None ,gender : str = 0 ):
    try:

        User(username=username,password=password,mobile=mobile,email=emile,gender=gender)


        await UserService.register(
            username=username,
            password=password,
            mobile=mobile,
            email=emile,
            gender=gender,
            config=settings
        )

        return SuccessResponse(msg="起号成功❤~")

    except Exception as e:
        return ErrorResponse(
            msg=str(e)
        )



