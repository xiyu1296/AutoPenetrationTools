import json
import secrets
import os
from datetime import datetime
from typing import Dict, Any, Optional

import requests  # ✅ 新增：用 requests 调 Dify

from fastapi import HTTPException

from api.v1.Penetration.crud import task_crud
from api.v1.tasks.schema import Budget

# =========================================================
# ✅ Dify 常量（按你的要求：直接写常量）
# =========================================================
DIFY_API_BASE = "http://baggiest-wade-untypically.ngrok-free.dev/v1"
DIFY_API_KEY = "test-key"
DIFY_WORKFLOW_ID = "f0fbd2cb-6b74-4e3c-b20f-9bcd106063b2"

# 推荐：run 接口不要长时间阻塞（你的 workflow 里有 HumanGate 的话 blocking 会卡住）
# 所以这里默认 streaming，并且“只读到拿到 workflow_run_id/task_id 就断开连接返回”
DIFY_RESPONSE_MODE = "streaming"

# requests 超时设置：连接超时 + 读超时
DIFY_CONNECT_TIMEOUT = 10
DIFY_READ_TIMEOUT = 30
# =========================================================


def _load_scope(task_id: str) -> Dict[str, Any]:
    """读取 runs/{task_id}/scope.json（create_task 里已经生成了）"""
    scope_path = f"runs/{task_id}/scope.json"
    if not os.path.exists(scope_path):
        raise HTTPException(status_code=404, detail=f"scope.json not found: {scope_path}")
    with open(scope_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_dify_inputs(scope: Dict[str, Any]) -> Dict[str, Any]:
    """
    按你 test_dify_workflow.py 的规范构造 inputs：
      inputs.target
      inputs.base_url
      inputs.timeout_seconds  (顶层)
      inputs.rate_limit_rps   (顶层)
    """
    budget = scope.get("budget") or {}
    target = scope.get("target")
    base_url = scope.get("base_url")

    if not target:
        raise HTTPException(status_code=422, detail="scope.json missing required field: target")
    if not base_url:
        # 你的 workflow 输入里 base_url 是必填时，这里就要强校验
        raise HTTPException(status_code=422, detail="scope.json missing required field: base_url")

    timeout_seconds = int(budget.get("timeout_seconds", 900))
    rate_limit_rps = budget.get("rate_limit_rps", 1.0)

    return {
        "target": target,
        "base_url": base_url,
        "timeout_seconds": timeout_seconds,
        "rate_limit_rps": rate_limit_rps,
    }


def trigger_dify_workflow(task_id: str, response_mode: str = DIFY_RESPONSE_MODE) -> Dict[str, Any]:
    """
    触发 Dify 工作流：
    - blocking：等最终结果返回（可能会因为 HumanGate 卡住，不推荐）
    - streaming：只要拿到 workflow_run_id / task_id 就立即返回（推荐）
    """
    scope = _load_scope(task_id)
    inputs = _build_dify_inputs(scope)

    payload = {
        "inputs": inputs,
        "response_mode": response_mode,
        "user": f"task_{task_id}",
    }

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }

    # ✅ 按你的脚本：/workflows/{WORKFLOW_ID}/run
    url = f"{DIFY_API_BASE.rstrip('/')}/workflows/{DIFY_WORKFLOW_ID}/run"

    # 记录文件：方便后续 status 查询/排障
    os.makedirs(f"runs/{task_id}", exist_ok=True)
    record_path = f"runs/{task_id}/dify_run.json"

    try:
        resp = requests.post(
            url,
            headers=headers,
            json=payload,
            stream=(response_mode == "streaming"),
            timeout=(DIFY_CONNECT_TIMEOUT, DIFY_READ_TIMEOUT),
        )
    except requests.exceptions.ConnectionError as e:
        raise HTTPException(status_code=502, detail=f"Cannot connect to Dify: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Dify request failed: {e}")

    if resp.status_code != 200:
        # 把错误也落盘
        err = {
            "task_id": task_id,
            "url": url,
            "status_code": resp.status_code,
            "error_text": resp.text,
            "payload": payload,
            "time": datetime.now().isoformat(),
        }
        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(err, f, ensure_ascii=False, indent=2)
        raise HTTPException(status_code=502, detail=f"Dify error {resp.status_code}: {resp.text}")

    # --------------------------
    # blocking：直接拿 json
    # --------------------------
    if response_mode == "blocking":
        result = resp.json()
        record = {
            "task_id": task_id,
            "mode": "blocking",
            "payload": payload,
            "result": result,
            "time": datetime.now().isoformat(),
        }
        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        return record

    # --------------------------
    # streaming：只读到拿到 ID 就返回
    # （你的脚本也是解析 data: 行来取 workflow_run_id / task_id）:contentReference[oaicite:3]{index=3}
    # --------------------------
    workflow_run_id = None
    dify_task_id = None

    try:
        for line in resp.iter_lines():
            if not line:
                continue
            if line.startswith(b"data: "):
                data_str = line[6:].decode("utf-8", errors="ignore")
                try:
                    evt = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                # 这两个字段你的脚本就是这么取的 :contentReference[oaicite:4]{index=4}
                if not workflow_run_id:
                    workflow_run_id = evt.get("workflow_run_id")
                if not dify_task_id:
                    dify_task_id = evt.get("task_id")

                # 一旦拿到任意一个就可以返回（通常第一批事件就有）
                if workflow_run_id or dify_task_id:
                    break
    finally:
        # 断开 SSE 连接：workflow 会继续在 Dify 后台跑
        resp.close()

    record = {
        "task_id": task_id,
        "mode": "streaming",
        "workflow_run_id": workflow_run_id,
        "dify_task_id": dify_task_id,
        "payload": payload,
        "time": datetime.now().isoformat(),
    }
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    return record

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

        run_request_path = f"runs/{task_id}/run_request.json"

        # 幂等：已经触发过就直接返回
        if os.path.exists(run_request_path):
            return {
                "task_id": task_id,
                "state": task.state,
                "message": "Task already triggered"
            }

        if task.state == "running":
            return {
                "task_id": task_id,
                "state": "running",
                "message": "Task already running"
            }

        # 2. 更新状态为 running
        task_crud.update(
            task_id,
            state="running",
            stage="stage0_triggered",
            percent=0,
            hint="Task triggered, waiting for Dify"
        )

        # 3. 记录运行开始
        os.makedirs(f"runs/{task_id}", exist_ok=True)
        run_record = {
            "task_id": task_id,
            "started_at": str(datetime.now()),
            "trigger": "manual"
        }
        with open(run_request_path, "w", encoding="utf-8") as f:
            json.dump(run_record, f, ensure_ascii=False, indent=2)

        # 4. ✅ 触发 Dify 工作流（按你的脚本逻辑）
        try:
            dify_record = trigger_dify_workflow(task_id, response_mode=DIFY_RESPONSE_MODE)

            # 更新状态：表示已经把 workflow 发出去了
            task_crud.update(
                task_id,
                stage="stage1_dify_started",
                percent=10,
                hint=f"Dify started: workflow_run_id={dify_record.get('workflow_run_id')} task_id={dify_record.get('dify_task_id')}",
            )

            return {
                "task_id": task_id,
                "state": "running",
                "workflow_run_id": dify_record.get("workflow_run_id"),
                "dify_task_id": dify_record.get("dify_task_id"),
                "message": "Task triggered; Dify workflow started"
            }

        except HTTPException:
            # 让 HTTPException 原样抛出
            raise
        except Exception as e:
            # 其它异常：标记任务失败
            task_crud.update(
                task_id,
                state="failed",
                stage="stage1_dify_failed",
                percent=0,
                hint=f"Dify trigger failed: {e}"
            )
            raise HTTPException(status_code=502, detail=f"Dify trigger failed: {e}")

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