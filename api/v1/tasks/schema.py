from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union


class Budget(BaseModel):
    """预算配置"""
    timeout_seconds: int = 900
    rate_limit_rps: float = 1.0


class ArtifactInfo(BaseModel):
    """制品信息"""
    name: str
    path: str
    mime_type: str
    size_bytes: int


class TaskApproveRequest(BaseModel):
    """审批任务请求"""
    task_id: str
    action: str  # approve | reject
    approver: str
    remark: Optional[str] = None


class ArtifactListResponse(BaseModel):
    """制品列表响应"""
    task_id: str
    artifacts: List[ArtifactInfo]


# ============ 任务调度相关 ============

class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    target: str
    base_url: Optional[str] = None
    budget: Union[Budget, Dict[str, Any], str]  # 兼容多种格式


# 上面是原有的，下面是新加的

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
    state: str  # created/running/blocked/done/failed
    stage: int  # 0-6
    progress: int  # 0-100
    message: Optional[str] = ""
    updated_at: str
