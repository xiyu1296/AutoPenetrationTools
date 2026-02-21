import json
import secrets
import os
from datetime import datetime  
from typing import Dict, Any, Optional

from fastapi import HTTPException

from api.v1.Penetration.crud import task_crud
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
        
        # 生成 scope.json
        scope_data = {
            "task_id": task_id,
            "target": target,
            "base_url": base_url,
            "budget": budget_obj.model_dump(),
            "created_at": datetime.now().isoformat()
        }
        
        os.makedirs(f"runs/{task_id}", exist_ok=True)
        with open(f"runs/{task_id}/scope.json", "w", encoding="utf-8") as f:
            json.dump(scope_data, f, ensure_ascii=False, indent=2)

        return {
            "task_id": task_id,
            "state": task.state,
            "created_at": task.updated_at
        }

    @staticmethod
    def run_task(task_id: str) -> Dict[str, Any]:
        """运行任务 - 只负责状态更新和触发（幂等）"""
        # 1. 校验任务存在
        task = task_crud.get(task_id)
        if not task:
            raise HTTPException(404, "task_id not found")
        
        # ===== 幂等检查（写文件记录） =====
        run_request_path = f"runs/{task_id}/run_request.json"
        
        # 检查是否已经运行过（有文件说明已经触发过）
        if os.path.exists(run_request_path):
            return {
                "task_id": task_id,
                "state": task.state,
                "message": "Task already triggered"
            }
        
        # 检查是否已经在运行状态
        if task.state == "running":
            return {
                "task_id": task_id,
                "state": "running",
                "message": "Task already running"
            }
        # ================================
        
        # 2. 更新状态为 running（stage0表示已触发）
        task_crud.update(
            task_id,
            state="running",
            stage="stage0_triggered",
            percent=0,
            hint="Task triggered, waiting for Dify"
        )
        
        # 3. 记录运行开始（写文件）
        os.makedirs(f"runs/{task_id}", exist_ok=True)
        run_record = {
            "task_id": task_id,
            "started_at": str(datetime.now()),
            "trigger": "manual"
        }
        with open(run_request_path, "w", encoding="utf-8") as f:
            json.dump(run_record, f, ensure_ascii=False, indent=2)
        
        # 4. 触发 Dify 工作流（如果有）
        # trigger_dify_workflow(task_id)
        
        return {
            "task_id": task_id,
            "state": "running",
            "message": "Task triggered, Dify will execute the workflow"
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

        # 生成 approval.json
        approval_data = {
            "task_id": task_id,
            "action": action,
            "approver": approver,
            "remark": remark,
            "time": datetime.now().isoformat()
        }
        
        os.makedirs(f"runs/{task_id}", exist_ok=True)
        with open(f"runs/{task_id}/approval.json", "w", encoding="utf-8") as f:
            json.dump(approval_data, f, ensure_ascii=False, indent=2)

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