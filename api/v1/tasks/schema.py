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


from typing import Dict, Any, List

class UnifiedToolRequest(BaseModel):
    """统一工具调用请求"""
    task_id: str
    tool_id: str               # 例如 "nuclei", "sqlmap"
    args: Dict[str, Any]       # 动态参数字典

class UnifiedToolResponse(BaseModel):
    """统一工具调用响应"""
    ok: bool
    tool_id: str
    summary: str               # 执行结果摘要
    findings: List[Dict[str, Any]] # 统一格式的漏洞/发现列表

class ToolNucleiRequest(BaseModel):
    """Nuclei 工具调用请求"""
    task_id: str
    targets: List[str]  # 直接接收待扫描的 URL 列表
    templates: Optional[List[str]] = ["cves/", "vulnerabilities/"] # 默认扫描高危模板

class NucleiFinding(BaseModel):
    """Nuclei 发现的漏洞条目"""
    target: str
    vulnerability: str
    severity: str
    evidence: str

class ToolNucleiResponse(BaseModel):
    """Nuclei 工具调用响应"""
    ok: bool
    findings: List[NucleiFinding]


class ToolSqlmapRequest(BaseModel):
    """SQLMap 工具调用请求"""
    task_id: str
    target_url: str  # 必须是带有参数的 URL，如 http://target/vuln.php?id=1
    risk_level: int = 1  # 测试风险等级 (1-3)

class SqlmapFinding(BaseModel):
    """SQLMap 发现的注入点及数据库信息"""
    url: str
    is_vulnerable: bool
    databases: List[str]
    evidence_log: str

class ToolSqlmapResponse(BaseModel):
    """SQLMap 工具调用响应"""
    ok: bool
    finding: SqlmapFinding


class DirScanFinding(BaseModel):
    """目录扫描发现的路径"""
    url: str
    status: int
    length: int
    title: str = ""


class ToolDirScanRequest(BaseModel):
    """目录扫描工具调用请求"""
    task_id: str
    target_url: str
    extensions: Optional[str] = "php,bak,zip,txt,env"
    wordlist_type: Optional[str] = "small"  # 允许值: small, medium, large, api

class ToolDirScanResponse(BaseModel):
    """目录扫描工具调用响应"""
    ok: bool
    findings: List[DirScanFinding]


class ToolHydraRequest(BaseModel):
    """Hydra 工具调用请求"""
    task_id: str
    target_ip: str    # 目标 IP，如 127.0.0.1
    service: str      # 服务协议，如 ssh, ftp, mysql, redis
    port: int         # 端口号，如 22, 21, 3306

class HydraFinding(BaseModel):
    """Hydra 爆破成功的凭证"""
    service: str
    ip: str
    port: int
    username: str
    password: str

class ToolHydraResponse(BaseModel):
    """Hydra 工具调用响应"""
    ok: bool
    is_cracked: bool
    findings: List[HydraFinding]