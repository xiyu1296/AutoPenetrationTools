import io
import zipfile
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response

from api.v1.tasks.schema import (
    TaskCreateRequest, TaskRunRequest, TaskStopRequest,
    TaskApproveRequest
)
from api.v1.tasks.service import task_service

# 配置
API_KEY = "test-key"  # Dify / 前端需要填同样的值（用于工具/任务接口鉴权）

# 创建FastAPI应用
taskRouter = APIRouter(
    prefix="/task",
    tags=["任务管理（生命周期）"],
)

penetrationRouter = APIRouter(
    prefix="/penetration",
    tags=["渗透测试工作流（工具接口供 Dify 调用）"],
)


def require_key(x_api_key: Optional[str]):
    """API密钥验证"""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: missing/invalid X-API-Key"
        )


def ok(msg: str, data=None):
    return {"success": True, "msg": msg, "data": data}


def fail(msg: str, data=None):
    return {"success": False, "msg": msg, "data": data}


@taskRouter.post("/create")
def create_task(
        req: TaskCreateRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """创建任务"""
    require_key(x_api_key)
    budget_obj = task_service.parse_budget(req.budget)
    data = task_service.create_task(req.target, req.base_url, budget_obj)
    return ok("created", data)


@taskRouter.post("/run")
def run_task(
        req: TaskRunRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """运行任务（转发到 app 的 run_by_task_id）"""
    require_key(x_api_key)
    data = task_service.run_task(req.task_id)
    return ok("running", data)


@taskRouter.get("/status")
def task_status(
        task_id: str,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """获取任务状态（真实查询 Dify workflow_run）"""
    require_key(x_api_key)
    data = task_service.get_status(task_id)
    return ok("ok", data)


@taskRouter.post("/stop")
def stop_task(
        req: TaskStopRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """停止任务（停止 Dify workflow task）"""
    require_key(x_api_key)
    data = task_service.stop_task(req.task_id)
    return ok("stopping", data)


@taskRouter.post("/approve")
def approve_task(
        req: TaskApproveRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """审批任务"""
    require_key(x_api_key)
    data = task_service.approve_task(req.task_id, req.action, req.approver, req.remark)
    return ok("ok", data)


@taskRouter.get("/artifacts/list")
def list_artifacts(
        task_id: str,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """列出制品"""
    require_key(x_api_key)
    data = task_service.list_artifacts(task_id)
    return ok("ok", data)


@taskRouter.get("/artifacts/download")
def download(
        task_id: str,
        path: str,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """下载制品（保持原来的 mock 下载行为不变）"""
    require_key(x_api_key)

    # 验证任务存在
    task_service.get_status(task_id)  # 会抛出404如果不存在

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", f"Mock download for {task_id}\nPath: {path}\n")
        z.writestr("scope.json", '{"mock": true, "note": "replace with real evidence later"}\n')
    mem.seek(0)

    return Response(content=mem.read(), media_type="application/zip")


from api.v1.Penetration.runner.httpx import HttpxRunner
from api.v1.Penetration.runner.nmap import NmapRunner
from api.v1.Penetration.runner.crawler import CrawlerRunner
from api.v1.Penetration.runner.candidate import CandidateRunner
from api.v1.Penetration.runner.validator import ValidatorRunner
from api.v1.Penetration.reporter import ReporterRunner


# 可选的其他端点

@penetrationRouter.post("/scan/nmap")
def scan_nmap(
        task_id: str,
        target: str,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """手动触发 Nmap 扫描并生成资产证据"""
    require_key(x_api_key)

    # 实例化并直接执行
    runner = NmapRunner(task_id)
    result = runner.scan(target)

    return {"ok": True, "data": result}





from api.v1.Penetration.runner.crawler import CrawlerRunner
from api.v1.Penetration.runner.candidate import CandidateRunner
from api.v1.Penetration.runner.validator import ValidatorRunner
from api.v1.Penetration.reporter import ReporterRunner

# 1. 补充 /probe/httpx 接口
@penetrationRouter.post("/probe/httpx")
def probe_httpx(task_id: str, x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    require_key(x_api_key)
    return {"ok": True, "data": HttpxRunner(task_id).run_fingerprint()}

# 2. 补充 /crawl 接口
@penetrationRouter.post("/crawl")
def crawl_endpoints(task_id: str, x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    require_key(x_api_key)
    return {"ok": True, "data": CrawlerRunner(task_id).run_crawl()}

# 3. 补充 /candidate/rule 接口
@penetrationRouter.post("/candidate/rule")
def candidate_rule(task_id: str, x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    require_key(x_api_key)
    return {"ok": True, "data": CandidateRunner(task_id).filter_candidates()}

# 4. 替换 /verify/controlled 的 Mock 实现
@penetrationRouter.post("/verify/controlled")
def verify_controlled(task_id: str, x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    require_key(x_api_key)
    return {"ok": True, "data": ValidatorRunner(task_id).verify()}

# 5. 替换 /report/render 的 Mock 实现
@penetrationRouter.post("/report/render")
def render_report(task_id: str, x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    require_key(x_api_key)
    return {"ok": True, "data": ReporterRunner(task_id).generate_final_package()}


from api.v1.tasks.schema import (ToolNucleiRequest, ToolNucleiResponse)
from api.v1.Penetration.runner.nuclei import NucleiRunner


@penetrationRouter.post("/tool/nuclei", response_model=ToolNucleiResponse)
def tool_nuclei_scan(
        req: ToolNucleiRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """
    独立工具调用：Nuclei 漏洞扫描
    Dify 可以直接传入疑似存在漏洞的 URL 列表进行扫描。
    """
    require_key(x_api_key)

    runner = NucleiRunner(req.task_id)
    findings = runner.run_scan(req.targets, req.templates)

    return ToolNucleiResponse(ok=True, findings=findings)


from api.v1.tasks.schema import ToolSqlmapRequest, ToolSqlmapResponse, SqlmapFinding
from api.v1.Penetration.runner.sqlmap import SqlmapRunner


@penetrationRouter.post("/tool/sqlmap", response_model=ToolSqlmapResponse)
def tool_sqlmap_scan(
        req: ToolSqlmapRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """
    独立工具调用：SQLMap 注入点探测
    Dify 可以在发现带参数的 URL 时主动调用此接口验证 SQL 注入漏洞。
    """
    require_key(x_api_key)

    runner = SqlmapRunner(req.task_id)
    result = runner.run_injection_test(req.target_url, req.risk_level)

    finding_obj = SqlmapFinding(**result)

    return ToolSqlmapResponse(ok=True, finding=finding_obj)


from api.v1.tasks.schema import ToolDirScanRequest, ToolDirScanResponse
from api.v1.Penetration.runner.dirscan import DirScanRunner


# api/v1/Penetration/tasks/controller.py (定位并替换 tool_dirscan 函数)

@penetrationRouter.post("/tool/dirscan", response_model=ToolDirScanResponse)
def tool_dirscan(
        req: ToolDirScanRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """
    独立工具调用：FFUF 目录扫描 (已集成 SecLists)
    """
    require_key(x_api_key)

    runner = DirScanRunner(req.task_id)
    findings = runner.run_scan(req.target_url, req.extensions, req.wordlist_type)

    return ToolDirScanResponse(ok=True, findings=findings)


from api.v1.tasks.schema import ToolHydraRequest, ToolHydraResponse, HydraFinding
from api.v1.Penetration.runner.hydra import HydraRunner


@penetrationRouter.post("/tool/hydra", response_model=ToolHydraResponse)
def tool_hydra_bruteforce(
        req: ToolHydraRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """
    独立工具调用：Hydra 弱口令爆破
    用于针对 SSH、FTP、MySQL、Redis 等协议进行密码暴力破解。
    """
    require_key(x_api_key)

    runner = HydraRunner(req.task_id)
    result = runner.run_bruteforce(req.target_ip, req.service, req.port)

    findings_objs = [HydraFinding(**f) for f in result.get("findings", [])]

    return ToolHydraResponse(
        ok=True,
        is_cracked=result.get("is_cracked", False),
        findings=findings_objs
    )