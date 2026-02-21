from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union


class Budget(BaseModel):
    """预算配置"""
    timeout_seconds: int = 900
    rate_limit_rps: float = 1.0


class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    target: str
    base_url: Optional[str] = None
    budget: Union[Budget, Dict[str, Any], str]  # 兼容多种格式


class TaskRunRequest(BaseModel):
    """运行任务请求"""
    task_id: str


class TaskStopRequest(BaseModel):
    """停止任务请求"""
    task_id: str


class TaskApproveRequest(BaseModel):
    """审批任务请求"""
    task_id: str
    action: str  # approve | reject
    approver: str
    remark: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    state: str
    stage: str
    progress: Dict[str, Any]
    blocked: Dict[str, Any]
    updated_at: str


class ArtifactInfo(BaseModel):
    """制品信息"""
    name: str
    path: str
    mime_type: str
    size_bytes: int


class ArtifactListResponse(BaseModel):
    """制品列表响应"""
    task_id: str
    artifacts: List[ArtifactInfo]