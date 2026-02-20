from app.core.base_model import ModelMixin
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String

from typing import List


class User(ModelMixin):
    __tablename__: str = "sys_user"
    __table_args__: dict[str, str] = {"comment": "用户表"}
    # __loader_options__

    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, comment="用户名", index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码")
    mobile: Mapped[str] = mapped_column(String(11), nullable=False, unique=True, comment="手机号", index=True)
    email: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, comment="邮箱", index=True)
    gender: Mapped[str | None] = mapped_column(String(1), default="0", nullable=True, comment="性别（1男、2女、0未知物种")
