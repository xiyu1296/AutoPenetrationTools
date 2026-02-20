import io
import zipfile
from typing import Optional, Dict, Any

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response

from api.v1.Penetration.runner.httpx import HttpxRunner
from api.v1.Penetration.runner.nmap import NmapRunner
from api.v1.tasks.schema import (
    TaskCreateRequest, TaskRunRequest,
    TaskApproveRequest
)
from api.v1.tasks.service import task_service

# 配置
API_KEY = "test-key"  # 你可以随便改；Dify 里要填同样的值

# 创建FastAPI应用
taskRouter = APIRouter(
    prefix="/task",
    tags=["任务管理"],
)

penetrationRouter = APIRouter(
    prefix="/penetration",
    tags=["渗透测试工作流"],
)


def require_key(x_api_key: Optional[str]):
    """API密钥验证"""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: missing/invalid X-API-Key"
        )


@taskRouter.post("/create")
def create_task(
        req: TaskCreateRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """创建任务"""
    require_key(x_api_key)

    # 解析budget
    budget_obj = task_service.parse_budget(req.budget)

    # 创建任务
    return task_service.create_task(req.target, req.base_url, budget_obj)


@taskRouter.post("/run")
def run_task(
        req: TaskRunRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """运行任务"""
    require_key(x_api_key)
    return task_service.run_task(req.task_id)


@taskRouter.get("/status")
def task_status(
        task_id: str,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """获取任务状态"""
    require_key(x_api_key)
    return task_service.get_status(task_id)


@taskRouter.post("/approve")
def approve_task(
        req: TaskApproveRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """审批任务"""
    require_key(x_api_key)
    return task_service.approve_task(
        req.task_id,
        req.action,
        req.approver,
        req.remark
    )


@taskRouter.get("/artifacts/list")
def list_artifacts(
        task_id: str,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """列出制品"""
    require_key(x_api_key)
    return task_service.list_artifacts(task_id)


@taskRouter.get("/artifacts/download")
def download(
        task_id: str,
        path: str,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """下载制品"""
    require_key(x_api_key)

    # 验证任务存在
    task_service.get_status(task_id)  # 会抛出404如果不存在

    # 返回一个zip文件
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", f"Mock download for {task_id}\nPath: {path}\n")
        z.writestr("scope.json", '{"mock": true, "note": "replace with real evidence later"}\n')
    mem.seek(0)

    return Response(content=mem.read(), media_type="application/zip")


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