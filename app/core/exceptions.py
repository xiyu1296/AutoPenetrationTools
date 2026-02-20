# -*- coding: utf-8 -*-

from typing import Any
from fastapi import FastAPI, Request, status

from app.common.constant import RET


class CustomException(Exception):
    """
    自定义异常基类
    """

    def __init__(
            self,
            msg: str = RET.EXCEPTION.msg,
            code: int = RET.EXCEPTION.code,
            success: bool = False
    ) -> None:
        """
        初始化异常对象。
        
        参数:
        - msg (str): 错误消息。
        - code (int): 业务状态码。
        - status_code (int): HTTP 状态码。
        - data (Any | None): 附加数据。
        - success (bool): 是否成功标记，默认 False。
        
        返回:
        - None
        """
        super().__init__(msg)  # 调用父类初始化方法
        self.code = code
        self.msg = msg
        self.success = success

    def __str__(self) -> str:
        """返回异常消息
        
        返回:
        - str: 异常消息
        """
        return self.msg
