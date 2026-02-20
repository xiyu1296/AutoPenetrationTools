
from fastapi import FastAPI,Request
from app.config.setting import Settings

from .crud import CRUD
from app.utils.hash_bcrpy_util import PwdUtil
from app.common.response import ErrorResponse,SuccessResponse
from app.core.exceptions import CustomException

class AuthService:


    @classmethod
    async def login(
            cls,
            request: Request,
            config: Settings,
            username : str|None = None,
            password : str|None = None,
    ):
        try:
            if username is None:
                raise CustomException(
                    msg= "请输入用户名"
                )
            if password is None:
                raise CustomException(
                    msg= "请输入密码"
                )
            else:
                try:
                    crud = CRUD(config=config)
                    pwd_hash = await crud.get_pwd(username = username)
                    print(pwd_hash)


                    if pwd_hash is None:
                        raise CustomException(
                            msg= "用户不存在"
                        )
                    if PwdUtil.verify_password(password, pwd_hash):
                        return None
                    else:
                        raise CustomException(
                            msg= "密码错误"
                        )
                except Exception as e:

                    raise CustomException(
                        msg= str(e)
                    )
        except Exception as e:
            raise CustomException(
                msg= str(e)
            )
