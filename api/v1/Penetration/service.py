import json
import secrets
from typing import Dict, Any, Optional, Tuple
from fastapi import HTTPException

from .schema import Budget, TaskCreateRequest
from .crud import task_crud


class TaskService:
    """任务业务逻辑"""


        # ============ 任务调度业务逻辑 ============

    async def create_orch_task(self, target: str, base_url: Optional[str] = None, budget: Optional[Dict] = None):
        """创建调度任务（生成task_id和目录）"""
        import uuid
        import os
        import json
        from datetime import datetime
        
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # 创建任务目录
        os.makedirs(f"runs/{task_id}", exist_ok=True)
        
        # 保存scope.json
        scope_data = {
            "task_id": task_id,
            "target": target,
            "base_url": base_url,
            "budget": budget or {"timeout_seconds": 300},
            "created_at": str(datetime.now())
        }
        with open(f"runs/{task_id}/scope.json", "w", encoding="utf-8") as f:
            json.dump(scope_data, f, ensure_ascii=False, indent=2)
        
        # 初始化状态文件
        await self.update_task_status(task_id, {
            "state": "created",
            "stage": 0,
            "progress": 0,
            "message": "任务创建成功"
        })
        
        return {"task_id": task_id, "status": "created"}

    async def update_task_status(self, task_id: str, status_data: dict):
        """更新任务状态到文件"""
        import os
        import json
        from datetime import datetime
        
        status_file = f"runs/{task_id}/status.json"
        
        # 读取现有状态或创建新的
        if os.path.exists(status_file):
            with open(status_file, "r", encoding="utf-8") as f:
                current = json.load(f)
        else:
            current = {
                "task_id": task_id,
                "state": "created",
                "stage": 0,
                "progress": 0,
                "metrics": {},
                "flags": {},
                "error": None,
                "message": ""
            }
        
        # 更新字段
        current.update(status_data)
        current["updated_at"] = str(datetime.now())
        
        # 保存
        os.makedirs(f"runs/{task_id}", exist_ok=True)
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)

    async def call_nmap_scan(self, task_id: str, target: str):
        """调用nmap扫描接口"""
        import httpx
        
        # 服务地址和API Key
        TOOL_RUNNER_URL = "http://127.0.0.1:8020"
        API_KEY = "test-key"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{TOOL_RUNNER_URL}/v1/penetration/scan/nmap",
                    headers={"X-API-Key": API_KEY},
                    json={"task_id": task_id, "target": target},
                    timeout=300
                )
                return response.json()
            except httpx.TimeoutException:
                return {"error": "timeout", "message": "端口扫描超时，目标可能无响应"}
            except Exception as e:
                return {"error": "failed", "message": str(e)}

    async def run_scan_task(self, task_id: str):
        """执行扫描任务（Stage1）"""
        import os
        import json
        
        # 检查任务是否存在
        if not os.path.exists(f"runs/{task_id}"):
            return {"error": "任务不存在"}
        
        # 读取target
        scope_file = f"runs/{task_id}/scope.json"
        if os.path.exists(scope_file):
            with open(scope_file, "r") as f:
                scope = json.load(f)
                target = scope.get("target", "127.0.0.1")
        else:
            target = "127.0.0.1"
        
        # 更新状态：开始扫描
        await self.update_task_status(task_id, {
            "state": "running",
            "stage": 1,
            "progress": 10,
            "message": "开始端口扫描"
        })
        
        # 调用扫描
        scan_result = await self.call_nmap_scan(task_id, target)
        
        # 检查错误
        if "error" in scan_result:
            error_msg = scan_result.get("message", "未知错误")
            allow_retry = scan_result.get("error") == "timeout"
            
            await self.update_task_status(task_id, {
                "state": "failed" if not allow_retry else "partial",
                "stage": 1,
                "progress": 0,
                "error": error_msg,
                "message": f"扫描失败: {error_msg}",
                "flags": {"allow_retry": allow_retry}
            })
            return {"status": "failed", "error": error_msg, "allow_retry": allow_retry}
        
        # 保存结果
        with open(f"runs/{task_id}/assets.json", "w", encoding="utf-8") as f:
            json.dump(scan_result, f, ensure_ascii=False, indent=2)
        
        # 统计端口数
        ports = scan_result.get("ports", [])
        port_count = len(ports)
        
        # 更新状态：完成
        await self.update_task_status(task_id, {
            "state": "running",
            "stage": 1,
            "progress": 100,
            "metrics": {"open_ports": port_count},
            "message": f"端口扫描完成，发现 {port_count} 个开放端口"
        })
        
        return {
            "status": "success",
            "task_id": task_id,
            "stage": 1,
            "progress": 100,
            "message": f"扫描完成，发现 {port_count} 个开放端口"
        }

    async def get_task_status(self, task_id: str):
        """获取任务状态"""
        import os
        import json
        
        status_file = f"runs/{task_id}/status.json"
        if os.path.exists(status_file):
            with open(status_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"error": "任务不存在"}

    async def approve_or_reject(self, task_id: str, req):
        """处理审批"""
        import os
        import json
        from datetime import datetime
        
        # 记录审批信息
        approval_record = {
            "task_id": task_id,
            "action": req.action,
            "approver": req.approver,
            "remark": req.remark,
            "time": str(datetime.now())
        }
        
        os.makedirs(f"runs/{task_id}", exist_ok=True)
        with open(f"runs/{task_id}/approval.json", "w", encoding="utf-8") as f:
            json.dump(approval_record, f, ensure_ascii=False, indent=2)
        
        # 更新状态
        if req.action == "approve":
            await self.update_task_status(task_id, {
                "state": "running",
                "message": "审批通过，任务继续"
            })
            return {"status": "approved", "message": "审批通过"}
        else:
            await self.update_task_status(task_id, {
                "state": "rejected",
                "message": f"审批拒绝: {req.remark}"
            })
            return {"status": "rejected", "message": "审批拒绝"}

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
        """运行任务"""
        task = task_crud.get(task_id)
        if not task:
            raise HTTPException(404, "task_id not found")

        # 更新任务状态
        task_crud.update(
            task_id,
            state="running",
            stage="stage1_scan",
            percent=25,
            hint="Scanning (mock)"
        )

        return {
            "task_id": task_id,
            "state": task.state,
            "message": "Task execution started"
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