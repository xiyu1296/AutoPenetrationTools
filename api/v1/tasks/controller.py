
from .schema import *
from .service import task_service


# ============ 以下是新加的代码 ============

from fastapi import APIRouter
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