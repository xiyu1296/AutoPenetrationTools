from pydantic import BaseModel,ConfigDict,Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..user.model import User

class AuthSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user:User|None = Field(default=None,description="用户信息")
    check_data_scope : bool = Field(default=False,description="检查是否有权限")
    db: AsyncSession = Field(description="数据库会话")