from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union, Literal


class Budget(BaseModel):
    """与 api/v1/tasks/schema.py 保持一致"""
    timeout_seconds: int = 900
    rate_limit_rps: float = 1.0


class AppTaskRunRequest(BaseModel):
    """前端一键运行入口：接收目标并启动 Dify Workflow"""
    target: str = Field(..., description="目标 URL / 域名 / IP")
    base_url: Optional[str] = Field(default=None, description="工具后端 base_url（会写入 scope.json，并传入 Dify inputs）")
    budget: Union[Budget, Dict[str, Any], str] = Field(default_factory=Budget, description="预算配置，支持对象/字典/JSON字符串")
    response_mode: Literal["streaming", "blocking"] = Field(default="streaming", description="Dify 执行模式")


class AppTaskRunByIdRequest(BaseModel):
    """仅内部/兼容用途：根据 task_id 触发 run 逻辑"""
    task_id: str
    response_mode: Literal["streaming", "blocking"] = Field(default="streaming")


class AppTaskApproveRequest(BaseModel):
    task_id: str
    action: Literal["approve", "reject"]
    approver: str
    remark: Optional[str] = None


class AppTaskStopRequest(BaseModel):
    task_id: str
