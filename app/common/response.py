from pydantic import BaseModel,Field
from fastapi.responses import JSONResponse

from .constant import RET

class ResponseSchema(BaseModel):
    msg : str = Field(default=RET.OK.msg, title="响应消息")
    code: int = Field(default=RET.OK.code, description="业务状态码")
    success : bool = Field(default=True, description="是否成功")



class SuccessResponse(JSONResponse):
    """
    成功响应
    """
    def __init__(
            self,
            msg: str = RET.OK.msg,
            code: int = RET.OK.code,
            success: bool = True,
    ):
        content = ResponseSchema(
            msg=msg,
            code=code,
            success=success,
        ).model_dump()
        super().__init__(content=content)



class ErrorResponse(JSONResponse):
    """
    错误响应
    """
    def __init__(
            self,
            msg: str = RET.EXCEPTION.msg,
            code: int = RET.EXCEPTION.code,
            success: bool = False,
    ):
        content = ResponseSchema(
            msg=msg,
            code=code,
            success=success,
        ).model_dump()
        super().__init__(content=content)