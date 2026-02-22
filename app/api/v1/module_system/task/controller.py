from typing import Optional

from fastapi import APIRouter

from app.config.setting import settings
from .service import TaskService
from .schame import AppTaskRunRequest, AppTaskRunByIdRequest, AppTaskStopRequest

# /system/task/*
task_router = APIRouter(prefix="/task", tags=["主程序入口（前端对接）"])
task_service = TaskService(settings)


def ok(msg: str, data=None):
    return {"success": True, "msg": msg, "data": data}


def fail(msg: str, data=None):
    return {"success": False, "msg": msg, "data": data}


@task_router.post("/run")
def run(req: AppTaskRunRequest):
    """
    前端入口：接收目标 -> 创建 task -> 触发 Dify workflow
    """
    try:
        data = task_service.run(
            target=req.target,
            base_url=req.base_url,
            budget_input=req.budget,
            response_mode=req.response_mode,
        )
        return ok("任务已启动", data)
    except Exception as e:
        return fail(str(e))


@task_router.post("/run_by_id")
def run_by_id(req: AppTaskRunByIdRequest):
    """
    兼容/内部入口：根据 task_id 触发 run（run 逻辑在 app）
    """
    try:
        data = task_service.run_by_task_id(req.task_id, response_mode=req.response_mode)
        return ok("ok", data)
    except Exception as e:
        return fail(str(e))


# 下面这些生命周期管理：不改逻辑，直接转发到 api/v1/tasks/service.py（真实 status/stop 在 api/tasks 实现）
@task_router.get("/status")
def status(task_id: str):
    try:
        from api.v1.tasks.service import task_service as api_task_service
        data = api_task_service.get_status(task_id)
        return ok("ok", data)
    except Exception as e:
        return fail(str(e))


@task_router.post("/stop")
def stop(req: AppTaskStopRequest):
    try:
        from api.v1.tasks.service import task_service as api_task_service
        data = api_task_service.stop_task(req.task_id)
        return ok("已请求停止", data)
    except Exception as e:
        return fail(str(e))


@task_router.post("/approve")
def approve(task_id: str, action: str, approver: str, remark: Optional[str] = None):
    try:
        from api.v1.tasks.service import task_service as api_task_service
        data = api_task_service.approve_task(task_id, action, approver, remark)
        return ok("ok", data)
    except Exception as e:
        return fail(str(e))


@task_router.get("/artifacts/list")
def list_artifacts(task_id: str):
    try:
        from api.v1.tasks.service import task_service as api_task_service
        data = api_task_service.list_artifacts(task_id)
        return ok("ok", data)
    except Exception as e:
        return fail(str(e))
