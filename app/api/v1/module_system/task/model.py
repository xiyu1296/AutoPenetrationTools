from app.core.base_model import ModelMixin
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String

from typing import List


class Task(ModelMixin):
    """
        需要的字段自己看着写
        ctrl点ModelMixin跳转查看预设好了的一些必要数据（这些不需要重复定义）
        别到时候给我整出俩个主键几个uuid之类的了！！！！
    """
    __tablename__: str = "sys_task"
    __table_args__: dict[str, str] = {"comment": "任务表"}