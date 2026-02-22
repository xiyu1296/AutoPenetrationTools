import json
import secrets
import os
from datetime import datetime


from typing import Dict, Any, Optional, Tuple

import requests
from fastapi import HTTPException

from api.v1.Penetration.crud import task_crud
from api.v1.Penetration.runner.base import BaseRunner
from api.v1.tasks.schema import Budget


# =========================================================
# Dify Service API config (按你要求：直接写常量)
# =========================================================
DIFY_API_BASE = "http://baggiest-wade-untypically.ngrok-free.dev/v1"
DIFY_API_KEY = "test-key"
DIFY_CONNECT_TIMEOUT = 10
DIFY_READ_TIMEOUT = 60
# =========================================================


def _dify_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }


def _dify_user(task_id: str) -> str:
    return f"task_{task_id}"


def _load_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _map_dify_status(dify_status: str) -> Tuple[str, str, int]:
    """
    Dify: running / succeeded / failed / stopped
    Local: running / completed / failed / stopped
    """
    s = (dify_status or "").lower()
    if s == "succeeded":
        return "completed", "dify_succeeded", 100
    if s == "failed":
        return "failed", "dify_failed", 100
    if s == "stopped":
        return "stopped", "dify_stopped", 100
    return "running", "dify_running", 30


class TaskService:
    """任务业务逻辑（生命周期管理留在 api/tasks）"""

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
        """
        运行任务（兼容旧 API）：run 逻辑已迁移到 app/module_system/task，
        这里做转发，保持 /v1/task/run 不崩。
        """
        from app.config.setting import settings
        from app.api.v1.module_system.task.service import TaskService as AppTaskService
        return AppTaskService(settings).run_by_task_id(task_id, response_mode="streaming")

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
    def _get_dify_detail(workflow_run_id: str) -> Dict[str, Any]:
        url = f"{DIFY_API_BASE.rstrip('/')}/workflows/run/{workflow_run_id}"
        try:
            resp = requests.get(
                url,
                headers=_dify_headers(),
                timeout=(DIFY_CONNECT_TIMEOUT, DIFY_READ_TIMEOUT),
            )
        except Exception as e:
            raise HTTPException(502, f"Query Dify run detail failed: {e}")

        if resp.status_code != 200:
            raise HTTPException(502, f"Dify run detail error {resp.status_code}: {resp.text}")
        return resp.json()

    @staticmethod
    def stop_task(task_id: str) -> Dict[str, Any]:
        """
        停止 Dify workflow task（需要 streaming 模式下拿到 dify_task_id）
        """
        dify_run = _load_json(f"runs/{task_id}/dify_run.json") or {}
        dify_task_id = dify_run.get("dify_task_id")
        user = dify_run.get("payload", {}).get("user") or dify_run.get("user") or _dify_user(task_id)

        if not dify_task_id:
            raise HTTPException(409, "No dify_task_id found. Ensure workflow started in streaming mode.")

        url = f"{DIFY_API_BASE.rstrip('/')}/workflows/tasks/{dify_task_id}/stop"
        try:
            resp = requests.post(
                url,
                headers=_dify_headers(),
                json={"user": user},
                timeout=(DIFY_CONNECT_TIMEOUT, DIFY_READ_TIMEOUT),
            )
        except Exception as e:
            raise HTTPException(502, f"Stop Dify task failed: {e}")

        if resp.status_code != 200:
            raise HTTPException(502, f"Dify stop error {resp.status_code}: {resp.text}")

        result = resp.json()
        _save_json(f"runs/{task_id}/dify_stop.json", {"result": result, "time": datetime.now().isoformat()})

        # update local state
        task_crud.update(task_id, state="stopped", stage="dify_stop_requested", percent=100, hint="Stop requested")
        BaseRunner(task_id).update_status({
            "state": "stopped",
            "stage": "dify_stop_requested",
            "percent": 100,
            "hint": f"Stop requested to Dify task_id={dify_task_id}",
            "blocked": {"is_blocked": False},
        })

        return {"task_id": task_id, "dify_task_id": dify_task_id, "result": result}


    @staticmethod
    def get_status(task_id: str) -> Dict[str, Any]:
        """获取任务状态（真实查询 Dify workflow_run 状态）"""
        task = task_crud.get(task_id)
        if not task:
            raise HTTPException(404, "task_id not found")

        # ===== 新增：读取 endpoints.json 统计端点数量 =====
        endpoints_count = 0
        crawler_name = "unknown"
        timebox = False
        partial = False

        endpoints_path = f"runs/{task_id}/endpoints.json"
        if os.path.exists(endpoints_path):
            try:
                with open(endpoints_path, 'r', encoding='utf-8') as f:
                    endpoints_data = json.load(f)
                    # 根据实际格式：{"task_id": "xxx", "endpoints": [...]}
                    endpoints_count = len(endpoints_data.get("endpoints", []))
                    # 如果以后有 crawler 字段可以加上，没有就用默认
                    crawler_name = endpoints_data.get("crawler", "unknown")
                    timebox = endpoints_data.get("timebox", False)
                    partial = endpoints_data.get("partial", False)
            except Exception as e:
                print(f"读取 endpoints.json 失败: {e}")
        # =============================================

        dify_run = _load_json(f"runs/{task_id}/dify_run.json") or {}
        workflow_run_id = dify_run.get("workflow_run_id")

        # 如果还没触发 dify（或没拿到 id），直接返回本地状态
        if not workflow_run_id:
            return {
                "task_id": task_id,
                "state": task.state,
                "stage": task.stage,
                "progress": {"percent": task.percent, "hint": task.hint},
                "blocked": task.blocked,
                "updated_at": task.updated_at,
                "metrics": {  # 新增
                    "endpoints": endpoints_count,
                    "crawler": crawler_name
                },
                "flags": {  # 新增
                    "timebox": timebox,
                    "partial": partial
                },
                "dify": {"workflow_run_id": None, "status": None, "outputs": None, "error": None},
            }

        detail = TaskService._get_dify_detail(workflow_run_id)
        _save_json(f"runs/{task_id}/dify_detail.json", detail)

        dify_status = detail.get("status")
        local_state, local_stage, percent = _map_dify_status(dify_status)

        hint = f"Dify status={dify_status}"
        if detail.get("elapsed_time") is not None:
            hint += f", elapsed={detail.get('elapsed_time')}s"
        if detail.get("error"):
            hint += f", error={detail.get('error')}"

        task_crud.update(
            task_id,
            state=local_state,
            stage=local_stage,
            percent=max(task.percent or 0, percent) if local_state == "running" else percent,
            hint=hint,
            blocked={"is_blocked": False},
        )

        BaseRunner(task_id).update_status({
            "state": local_state,
            "stage": local_stage,
            "percent": max(int(getattr(task, "percent", 0) or 0), percent) if local_state == "running" else percent,
            "hint": hint,
            "blocked": {"is_blocked": False},
        })

        task = task_crud.get(task_id)
        return {
            "task_id": task_id,
            "state": task.state,
            "stage": task.stage,
            "progress": {"percent": task.percent, "hint": task.hint},
            "blocked": task.blocked,
            "updated_at": task.updated_at,
            "metrics": {  # 新增
                "endpoints": endpoints_count,
                "crawler": crawler_name
            },
            "flags": {  # 新增
                "timebox": timebox,
                "partial": partial
            },
            "dify": {
                "workflow_run_id": workflow_run_id,
                "workflow_id": detail.get("workflow_id"),
                "status": dify_status,
                "inputs": detail.get("inputs"),
                "outputs": detail.get("outputs"),
                "error": detail.get("error"),
                "created_at": detail.get("created_at"),
                "finished_at": detail.get("finished_at"),
                "elapsed_time": detail.get("elapsed_time"),
            },
        }

    @staticmethod
    def approve_task(task_id: str, action: str, approver: str, remark: Optional[str]) -> Dict[str, Any]:
        """审批任务（reject 不 stop Dify；仅跳过后续验证）"""
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

        update_data = {"approved": action, "blocked": {"is_blocked": False}}

        if action == "approve":
            update_data.update({
                "state": "running",
                "stage": "approved",
                "percent": max(task.percent or 0, 60),
                "hint": "Approved (service side). If Dify is waiting on Human Input, approve in Dify WebApp.",
            })
            msg = "Approval accepted"
        else:
            # reject：不再 stop Dify（Dify 会走 REJECT 分支继续产出报告）
            update_data.update({
                "state": "running",
                "stage": "rejected",
                "percent": 100,
                "hint": "Rejected; skip further verification, Dify will still generate report",
            })
            msg = "Rejected; stop requested"

        task_crud.update(task_id, **update_data)

        return {"task_id": task_id, "state": update_data["state"], "message": msg}

    @staticmethod
    def list_artifacts(task_id: str) -> Dict[str, Any]:
        """列出制品（真实扫描 runs/{task_id}）"""
        task = task_crud.get(task_id)
        if not task:
            raise HTTPException(404, "task_id not found")

        base_dir = f"runs/{task_id}"
        artifacts = []
        if os.path.exists(base_dir):
            for fn in sorted(os.listdir(base_dir)):
                p = os.path.join(base_dir, fn)
                if os.path.isfile(p):
                    mime = "application/octet-stream"
                    if fn.endswith(".json"):
                        mime = "application/json"
                    elif fn.endswith(".md"):
                        mime = "text/markdown"
                    elif fn.endswith(".zip"):
                        mime = "application/zip"
                    artifacts.append({
                        "name": fn,
                        "path": p,
                        "mime_type": mime,
                        "size_bytes": os.path.getsize(p),
                    })

        # include dify outputs paths if exist
        detail = _load_json(f"runs/{task_id}/dify_detail.json") or {}
        outputs = detail.get("outputs") or {}
        if isinstance(outputs, dict):
            for key in ("report_path", "zip_path"):
                if outputs.get(key):
                    artifacts.append({
                        "name": key,
                        "path": outputs[key],
                        "mime_type": "application/octet-stream",
                        "size_bytes": 0,
                    })

        return {"task_id": task_id, "artifacts": artifacts}


# 服务实例
task_service = TaskService()