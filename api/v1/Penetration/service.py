import json
import secrets
from typing import Dict, Any, Optional, Tuple
from fastapi import HTTPException

from .schema import Budget, TaskCreateRequest
from .crud import task_crud
from .runner.nmap import NmapRunner


class TaskService:
    """任务业务逻辑"""

    @staticmethod
    def parse_budget(budget_input: Any) -> Budget:
        """解析budget参数（兼容多种格式）"""
        if isinstance(budget_input, Budget):
            return budget_input
        elif isinstance(budget_input, str):
            try:
                budget_dict = json.loads(budget_input)
            except Exception as e:
                raise HTTPException(
                    status_code=422,
                    detail=f"budget must be a JSON object string: {e}"
                )
            return Budget(**budget_dict)
        elif isinstance(budget_input, dict):
            return Budget(**budget_input)
        else:
            raise HTTPException(
                status_code=422,
                detail="budget must be an object or JSON object string"
            )

    @staticmethod
    def create_task(target: str, base_url: Optional[str], budget_obj: Budget) -> Dict[str, Any]:
        """创建新任务"""
        task_id = "t_" + secrets.token_hex(4)
        task = task_crud.create(task_id, budget_obj.model_dump())

        return {
            "task_id": task_id,
            "state": task.state,
            "created_at": task.updated_at
        }

    @staticmethod
    def run_task(task_id: str) -> Dict[str, Any]:
        """运行任务：触发 S3 Runner 的物理执行"""
        task = task_crud.get(task_id)
        if not task:
            raise HTTPException(404, "task_id not found")

        # 1. 更新内存状态
        task_crud.update(task_id, state="running", stage="stage1_scan", percent=10)

        # 2. 实例化并启动物理扫描器
        # 注意：此处应根据实际架构决定是否使用 BackgroundTasks
        target = task.budget.get("target", "127.0.0.1")
        runner = NmapRunner(task_id)
        runner.scan(target)

        return {
            "task_id": task_id,
            "state": "running",
            "message": "任务已启动，物理扫描中"
        }


    @staticmethod
    def get_status(task_id: str) -> Dict[str, Any]:
        """获取任务状态（包含进度模拟）"""
        task = task_crud.get(task_id)
        if not task:
            raise HTTPException(404, "task_id not found")

        # 模拟进度 -> 最终进入审批阻塞状态
        if task.state == "running":
            task.poll_count += 1
            if task.poll_count >= 2 and task.approved is None:
                task_crud.update(
                    task_id,
                    state="blocked",
                    stage="human_gate",
                    percent=60,
                    hint="Waiting for approval (mock)",
                    blocked={
                        "is_blocked": True,
                        "reason": "Needs approval to proceed",
                        "required_action": "approve_or_reject",
                    }
                )
            else:
                task_crud.update(task_id)  # 只更新时间戳

        task = task_crud.get(task_id)  # 重新获取最新状态
        return {
            "task_id": task_id,
            "state": task.state,
            "stage": task.stage,
            "progress": {"percent": task.percent, "hint": task.hint},
            "blocked": task.blocked,
            "updated_at": task.updated_at,
        }

    @staticmethod
    def approve_task(task_id: str, action: str, approver: str, remark: Optional[str]) -> Dict[str, Any]:
        """审批任务"""
        task = task_crud.get(task_id)
        if not task:
            raise HTTPException(404, "task_id not found")

        if action not in ("approve", "reject"):
            raise HTTPException(400, "action must be approve or reject")

        update_data = {"approved": action}

        if action == "approve":
            update_data.update({
                "state": "running",
                "stage": "stage5_verify",
                "percent": 80,
                "hint": "Verifying (mock)",
                "blocked": {"is_blocked": False}
            })
            msg = "Approval accepted, task unblocked"
        else:  # reject
            update_data.update({
                "state": "completed",
                "stage": "stage7_report",
                "percent": 100,
                "hint": "Rejected; report only (mock)",
                "blocked": {"is_blocked": False}
            })
            msg = "Rejected; task finished with report only"

        task_crud.update(task_id, **update_data)

        return {
            "task_id": task_id,
            "state": update_data["state"],
            "message": msg
        }

    @staticmethod
    def list_artifacts(task_id: str) -> Dict[str, Any]:
        """列出制品"""
        task = task_crud.get(task_id)
        if not task:
            raise HTTPException(404, "task_id not found")

        return {
            "task_id": task_id,
            "artifacts": [
                {
                    "name": "scope.json",
                    "path": f"runs/{task_id}/scope.json",
                    "mime_type": "application/json",
                    "size_bytes": 200
                },
                {
                    "name": "download.zip",
                    "path": f"runs/{task_id}/download.zip",
                    "mime_type": "application/zip",
                    "size_bytes": 800
                },
            ]
        }

# 服务实例
task_service = TaskService()