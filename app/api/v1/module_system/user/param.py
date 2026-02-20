from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.core.exceptions import CustomException


class User(BaseModel):
    username: Optional[str] = None
    password: Optional[str]
    email: Optional[str]
    mobile: Optional[str]
    gender: Optional[str]

    # 手机号格式验证
    @field_validator('mobile')
    @classmethod
    def validate_mobile(cls, v: str) -> Optional[str]:
        if not v.isdigit():
            raise CustomException("auv,您这儿手机号还有洋文儿啊")
        if len(v) < 11:
            raise CustomException("auv,您这骨灰用户儿，手机号位数这么少")
        if len(v) > 11:
            raise CustomException("auv,您这未来人儿啊，手机号位数这么长")
        if not v.startswith('1'):
            raise CustomException("auv,您这儿手机号开头儿真稀罕儿")

        operators = [
            '3', '4', '5', '6', '7', '8', '9'
        ]

        if len(v) >= 2 and v[1] not in operators:
            raise CustomException("auv,您这儿是外星运营商的电话卡呀")

    # 邮箱格式验证
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v

        # 使用正则表达式验证邮箱格式
        import re
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]+$'
        if not re.match(pattern, v):
            raise CustomException("auv,您这邮箱能送多少光年儿去？")
        return v

    # 性别格式验证
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v: str) -> Optional[str]:
        if v not in ['0', '1', '2']:
            raise CustomException("auv,你这是人类吗？")

    # 密码格式验证


class SearchChioce(BaseModel):
    choice: str
