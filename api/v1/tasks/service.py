import json
import secrets
from typing import Dict, Any, Optional

from fastapi import HTTPException

from api.v1.Penetration.crud import task_crud
from api.v1.Penetration.reporter import ReporterRunner
from api.v1.Penetration.runner.candidate import CandidateRunner
from api.v1.Penetration.runner.crawler import CrawlerRunner
from api.v1.Penetration.runner.httpx import HttpxRunner
from api.v1.Penetration.runner.nmap import NmapRunner
from api.v1.Penetration.runner.validator import ValidatorRunner
from api.v1.tasks.schema import Budget


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

        # 初始化物理目录并注入预算合同
        from api.v1.Penetration.runner.base import BaseRunner
        runner = BaseRunner(task_id)
        runner.update_status({
            "target": target,
            "budget": budget_obj.model_dump()
        })

        return {
            "task_id": task_id,
            "state": task.state,
            "created_at": task.updated_at
        }

    @staticmethod
    def run_task(task_id: str):
        # 1. 侦察阶段
        NmapRunner(task_id).scan("127.0.0.1", ports="8080")
        HttpxRunner(task_id).run_fingerprint()

        # 2. 挖掘阶段
        CrawlerRunner(task_id).run_crawl()
        CandidateRunner(task_id).filter_candidates()

        # 3. 验证与交付阶段
        ValidatorRunner(task_id).verify()
        ReporterRunner(task_id).generate_final_package()

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
