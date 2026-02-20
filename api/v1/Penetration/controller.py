from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response
from typing import Optional, Dict, Any
import io
import zipfile

from .schema import (
    TaskCreateRequest, TaskRunRequest,
    TaskApproveRequest, Budget
)
from .service import task_service

# 配置
API_KEY = "test-key"  # 你可以随便改；Dify 里要填同样的值

# 创建FastAPI应用
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


@penetrationRouter.post("/task/create")
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


@penetrationRouter.post("/task/run")
def run_task(
        req: TaskRunRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """运行任务"""
    require_key(x_api_key)
    return task_service.run_task(req.task_id)


@penetrationRouter.get("/task/status")
def task_status(
        task_id: str,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """获取任务状态"""
    require_key(x_api_key)
    return task_service.get_status(task_id)


@penetrationRouter.post("/task/approve")
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


@penetrationRouter.get("/artifacts/list")
def list_artifacts(
        task_id: str,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """列出制品"""
    require_key(x_api_key)
    return task_service.list_artifacts(task_id)


@penetrationRouter.get("/artifacts/download")
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
        payload: Dict[str, Any],
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """模拟nmap扫描"""
    require_key(x_api_key)
    return {"ok": True, "message": "scan done (mock)"}


@penetrationRouter.post("/verify/controlled")
def verify_controlled(
        payload: Dict[str, Any],
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """模拟验证"""
    require_key(x_api_key)
    return {"ok": True, "message": "verify done (mock)"}


@penetrationRouter.post("/report/render")
def render_report(
        payload: Dict[str, Any],
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
):
    """模拟报告生成"""
    require_key(x_api_key)
    return {"ok": True, "message": "report done (mock)"}


# ============ 以下是新加的代码 ============

from fastapi import APIRouter
import json
import os

# 创建任务调度路由器
task_router = APIRouter(prefix="/tasks", tags=["任务调度"])

@task_router.post("")
async def create_task(req: TaskCreateRequest):
    """创建新任务"""
    result = await task_service.create_orch_task(
        req.target, req.base_url, req.budget
    )
    return result

@task_router.get("/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    result = await task_service.get_task_status(task_id)
    return result

@task_router.post("/{task_id}/run")
async def run_task(task_id: str):
    """运行任务"""
    result = await task_service.run_scan_task(task_id)
    return result

@task_router.post("/{task_id}/approve")
async def approve_task(task_id: str, req: TaskApproveRequest):
    """审批任务"""
    result = await task_service.approve_or_reject(task_id, req)
    return result

@task_router.get("/{task_id}/download.zip")
async def download_zip(task_id: str):
    """下载产物包"""
    from fastapi.responses import FileResponse
    import zipfile
    import tempfile
    
    task_dir = f"runs/{task_id}"
    if not os.path.exists(task_dir):
        return {"error": "任务不存在"}
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        with zipfile.ZipFile(tmp.name, 'w') as zf:
            for root, dirs, files in os.walk(task_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, task_dir)
                    zf.write(file_path, arcname)
        
        return FileResponse(
            tmp.name,
            media_type='application/zip',
            filename=f"{task_id}_artifacts.zip"
        )

@task_router.get("/{task_id}/artifacts")
async def list_artifacts(task_id: str):
    """列出所有产物文件"""
    task_dir = f"runs/{task_id}"
    if not os.path.exists(task_dir):
        return {"error": "任务不存在"}
    
    artifacts = []
    for file in os.listdir(task_dir):
        file_path = os.path.join(task_dir, file)
        artifacts.append({
            "filename": file,
            "size": os.path.getsize(file_path),
            "path": file_path
        })
    
    return {"task_id": task_id, "artifacts": artifacts}