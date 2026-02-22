import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException

from app.config.setting import Settings
from .schame import Budget

# Reuse existing task lifecycle CRUD & evidence store
from api.v1.Penetration.crud import task_crud
from api.v1.Penetration.runner.base import BaseRunner

# =========================================================
# Dify Service API config (按你要求：常量写在文件最前面即可)
# =========================================================
DIFY_API_BASE = "http://baggiest-wade-untypically.ngrok-free.dev/v1"
DIFY_API_KEY = "test-key"
# TODO: 替换成你实际发布的 workflow id
DIFY_WORKFLOW_ID = "f0fbd2cb-6b74-4e3c-b20f-9bcd106063b2"

DIFY_CONNECT_TIMEOUT = 10
DIFY_READ_TIMEOUT = 60
# =========================================================


def _dify_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }


def _dify_user(task_id: str) -> str:
    # stop 接口需要 user，必须保持一致
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


def _parse_budget(budget_input: Any) -> Budget:
    if isinstance(budget_input, Budget):
        return budget_input
    if isinstance(budget_input, str):
        try:
            obj = json.loads(budget_input)
        except Exception as e:
            raise HTTPException(422, f"budget must be JSON string: {e}")
        return Budget(**obj)
    if isinstance(budget_input, dict):
        return Budget(**budget_input)
    return Budget()


class TaskService:
    """
        这里是主要逻辑了，实现几个方法就行了应该是
    """

    def __init__(self, config: Settings):
        self.config = config

    # ------------------------------
    # 你要迁移的：run 逻辑（原来在 api/v1/tasks/service.py 的 run_task）
    # ------------------------------
    def run_by_task_id(self, task_id: str, response_mode: str = "streaming") -> Dict[str, Any]:
        """
        迁移后的 run 逻辑：只负责状态更新 + 幂等 + 触发 Dify
        """
        # 1. 校验任务存在（复用原 task_crud）
        task = task_crud.get(task_id)
        if not task:
            raise HTTPException(404, "task_id not found")

        run_request_path = f"runs/{task_id}/run_request.json"

        # 幂等：有文件说明已经触发过
        if os.path.exists(run_request_path):
            dify_run = _load_json(f"runs/{task_id}/dify_run.json") or {}
            return {
                "task_id": task_id,
                "state": task.state,
                "workflow_run_id": dify_run.get("workflow_run_id"),
                "dify_task_id": dify_run.get("dify_task_id"),
                "message": "Task already triggered"
            }

        # 已经 running
        if task.state == "running":
            return {"task_id": task_id, "state": "running", "message": "Task already running"}

        # 2. 更新状态为 running
        task_crud.update(
            task_id,
            state="running",
            stage="stage0_triggered",
            percent=0,
            hint="Task triggered, calling Dify"
        )

        # 同步物理 status.json（让前端也能从 runs 读到状态）
        BaseRunner(task_id).update_status({
            "state": "running",
            "stage": "Stage0_Triggered",
            "percent": 5,
            "hint": "任务已触发，开始调用 Dify 工作流",
            "blocked": {"is_blocked": False},
        })

        # 3. 记录运行开始
        os.makedirs(f"runs/{task_id}", exist_ok=True)
        run_record = {
            "task_id": task_id,
            "started_at": datetime.now().isoformat(),
            "trigger": "app"
        }
        _save_json(run_request_path, run_record)

        # 4. 触发 Dify workflow（核心：调用 dify service api）
        try:
            dify_record = self._trigger_dify_workflow(task_id, response_mode=response_mode)
        except Exception as e:
            # ===== 失败回滚：把任务标记为 failed，并删除 run_request 允许重试 =====
            try:
                task_crud.update(
                    task_id,
                    state="failed",
                    stage="stage1_dify_failed",
                    percent=100,
                    hint=f"Dify 调用失败: {e}",
                    blocked={"is_blocked": False},
                )
            except Exception:
                pass
            try:
                BaseRunner(task_id).update_status({
                    "state": "failed",
                    "stage": "Stage1_DifyFailed",
                    "percent": 100,
                    "hint": f"Dify 调用失败: {e}",
                    "blocked": {"is_blocked": False},
                })
            except Exception:
                pass
            try:
                _save_json(f"runs/{task_id}/dify_error.json", {"error": str(e), "time": datetime.now().isoformat()})
            except Exception:
                pass
            try:
                if os.path.exists(run_request_path):
                    os.remove(run_request_path)
            except Exception:
                pass
            raise

        task_crud.update(
            task_id,
            stage="stage1_dify_started",
            percent=10,
            hint=f"Dify started: workflow_run_id={dify_record.get('workflow_run_id')} dify_task_id={dify_record.get('dify_task_id')}",
        )

        BaseRunner(task_id).update_status({
            "stage": "Stage1_DifyStarted",
            "percent": 10,
            "hint": f"Dify started: workflow_run_id={dify_record.get('workflow_run_id')} dify_task_id={dify_record.get('dify_task_id')}",
        })

        return {
            "task_id": task_id,
            "state": "running",
            "workflow_run_id": dify_record.get("workflow_run_id"),
            "dify_task_id": dify_record.get("dify_task_id"),
            "message": "Task triggered; Dify workflow started"
        }

    def run(self, target: str, base_url: Optional[str], budget_input: Any, response_mode: str = "streaming") -> Dict[str, Any]:
        """
        前端主入口：接收 target -> 复用 api/v1/tasks 的 create_task 创建 task_id -> 调用 run_by_task_id
        """
        # 复用 api/v1/tasks 的预算解析逻辑：这里直接做同等解析，避免循环依赖
        budget = _parse_budget(budget_input)

        # 复用 api/v1/tasks/service.create_task（生命周期管理不动）
        from api.v1.tasks.service import task_service as api_task_service
        create_res = api_task_service.create_task(target, base_url, budget)

        task_id = create_res["task_id"]
        run_res = self.run_by_task_id(task_id, response_mode=response_mode)

        # 给前端返回 task_id + 轮询入口
        run_res.update({
            "status_url": f"/v1/task/status?task_id={task_id}",  # 兼容旧接口
            "app_status_url": f"/system/task/status?task_id={task_id}",  # 新 app 入口
        })
        return run_res

    # ------------------------------
    # Dify 调用封装（你之前脚本已验证可用）
    # ------------------------------
    def _trigger_dify_workflow(self, task_id: str, response_mode: str = "streaming") -> Dict[str, Any]:
        scope = _load_json(f"runs/{task_id}/scope.json") or {}
        budget = scope.get("budget") or {}

        inputs = {
            "target": scope.get("target"),
            "base_url": scope.get("base_url"),
            "timeout_seconds": int(budget.get("timeout_seconds", 900)),
            "rate_limit_rps": float(budget.get("rate_limit_rps", 1.0)),
        }
        if not inputs["target"]:
            raise HTTPException(422, "scope.json missing required field: target")

        payload = {
            "inputs": inputs,
            "response_mode": response_mode,
            "user": _dify_user(task_id),
        }

        # 兼容两种路径：你脚本跑通的是 /workflows/{workflow_id}/run
        primary_url = f"{DIFY_API_BASE.rstrip('/')}/workflows/{DIFY_WORKFLOW_ID}/run"
        fallback_url = f"{DIFY_API_BASE.rstrip('/')}/workflows/run"

        def _post(url: str) -> requests.Response:
            return requests.post(
                url,
                headers=_dify_headers(),
                json=payload,
                stream=(response_mode == "streaming"),
                timeout=(DIFY_CONNECT_TIMEOUT, DIFY_READ_TIMEOUT),
            )

        try:
            resp = _post(primary_url)
            if resp.status_code == 404:
                resp.close()
                resp = _post(fallback_url)
        except Exception as e:
            raise HTTPException(502, f"Call Dify failed: {e}")

        if resp.status_code != 200:
            raise HTTPException(502, f"Dify error {resp.status_code}: {resp.text}")

        # blocking：直接返回 JSON
        if response_mode == "blocking":
            result = resp.json()
            record = {
                "task_id": task_id,
                "mode": "blocking",
                "payload": payload,
                "raw": result,
                "workflow_run_id": result.get("workflow_run_id") or result.get("data", {}).get("id"),
                "dify_task_id": result.get("task_id"),
                "time": datetime.now().isoformat(),
            }
            _save_json(f"runs/{task_id}/dify_run.json", record)
            return record

        # streaming：解析 SSE data: 行，拿到 workflow_run_id / task_id 即返回
        workflow_run_id = None
        dify_task_id = None
        try:
            for line in resp.iter_lines():
                if not line:
                    continue
                if line.startswith(b"data: "):
                    s = line[6:].decode("utf-8", errors="ignore")
                    try:
                        evt = json.loads(s)
                    except json.JSONDecodeError:
                        continue
                    if not workflow_run_id:
                        workflow_run_id = evt.get("workflow_run_id")
                    if not dify_task_id:
                        dify_task_id = evt.get("task_id")
                    if workflow_run_id or dify_task_id:
                        break
        finally:
            resp.close()

        record = {
            "task_id": task_id,
            "mode": "streaming",
            "payload": payload,
            "workflow_run_id": workflow_run_id,
            "dify_task_id": dify_task_id,
            "time": datetime.now().isoformat(),
        }
        _save_json(f"runs/{task_id}/dify_run.json", record)
        return record

    def create_report(self):
        """
            生成报告(这个你可以使用模板，写一个规定好格式的docs文件，然后进行关键字替换，这样既保证了字体统一，也保证了格式的确定性和自定义的简单，具体的关键词替换和设定，要ai帮你）
        """
        pass

    def save_task(self):
        """
            保存任务数据到数据库
        """
        pass
