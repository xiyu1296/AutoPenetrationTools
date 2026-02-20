import traceback
import sys

from app.config.setting import Settings
from .crud import UserCRUD
from app.utils.hash_bcrpy_util import PwdUtil

from app.core.exceptions import CustomException


class UserService:
    def __init__(self, config: Settings):
        self.config = config

    @classmethod
    async def register(cls, username: str, password: str, email: str, mobile: str | None, gender: str,
                       config: Settings):

        try:
            # 2. 构建user字典
            user = {
                "username": username,
                "password": PwdUtil.set_password_hash(password),
                "mobile": mobile,
                "email": email,
                "gender": gender
            }
            # 创建UserCRUD实例
            try:
                usercrud = UserCRUD(config)
            except Exception as e:
                raise EOFError(f"无法创建UserCRUD实例: {str(e)}")

            # 判断是否有重复用户名
            try:
                print("开始检查用户名")
                check_username = await usercrud.check_username(username=username)
                if not check_username:
                    raise CustomException(
                        msg="亲，咱这不让同名同姓哦~❤"
                    )
            except Exception as e:
                raise EOFError(f"重复用户名检测失败: {str(e)}")

            # 判断是否有重复手机号
            try:
                print("开始检查手机号")
                check_mobile = await usercrud.check_mobile(mobile=mobile)
                if not check_mobile:
                    raise CustomException(
                        msg="亲，咱这不让开小号哦~❤"
                    )
            except Exception as e:
                raise EOFError(f"重复电话号检测失败: {str(e)}")

            # 4. 调用create_user方法
            try:
                await usercrud.create_user(user=user)
                return True

            except Exception as e:
                # # 获取详细的异常信息
                # exc_type, exc_value, exc_tb = sys.exc_info()
                #
                # # 打印调用栈
                # tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
                # for line in tb_lines:
                #     print(f"    {line}", end="")
                #
                # raise EOFError(f"无法调用create_user方法: {str(e)}")
                raise CustomException(
                    msg="注册失败,请找找管理员"
                )

        except Exception as e:

            error_info = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "location": "UserService.register",
                "traceback": traceback.format_exc(),
                "input_data": {
                    "username": username,
                    "phone": mobile,
                    "has_emile": email is not None
                }

            }

            raise CustomException(
                msg=f"注册失败: {type(e).__name__}: {str(e)}",
            )
