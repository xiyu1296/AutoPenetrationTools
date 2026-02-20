from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    target: str
    base_url: Optional[str] = None
    budget: Optional[Dict[str, Any]] = None


class TaskRunRequest(BaseModel):
    """运行任务请求"""
    task_id: str


class ApproveRequest(BaseModel):
    """审批请求"""
    action: str  # approve 或 reject
    approver: str  # 审批人
    remark: Optional[str] = ""


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    state: str  # created/running/blocked/done/failed/partial
    stage: int  # 0-6
    progress: int  # 0-100
    message: Optional[str] = ""
    updated_at: str