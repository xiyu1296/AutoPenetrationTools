import json
import uuid
import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from asyncio import Queue

from .schema import TaskCreateRequest


class TaskService:
    """任务调度业务逻辑"""

    def __init__(self):
        # ============ 排队并发控制 ============
        self.MAX_CONCURRENT = 3  # 最多同时跑3个任务
        self.running_tasks: Dict[str, str] = {}  # 正在跑的任务
        self.task_queue = Queue()  # 排队队列
        self.TOOL_RUNNER_URL = "http://127.0.0.1:8020"
        self.API_KEY = "test-key"

    # ============ 任务状态管理 ============

    async def update_task_status(self, task_id: str, status_data: dict):
        """更新任务状态到文件"""
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

    async def get_task_status(self, task_id: str):
        """获取任务状态"""
        status_file = f"runs/{task_id}/status.json"
        if os.path.exists(status_file):
            with open(status_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "task_id": task_id,
            "state": "not_found",
            "stage": 0,
            "progress": 0,
            "message": "任务不存在",
            "updated_at": str(datetime.now())
        }

    # ============ 任务创建 ============

    async def create_orch_task(self, target: str, base_url: Optional[str] = None, budget: Optional[Dict] = None):
        """创建调度任务（生成task_id和目录）"""
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

    # ============ 端口扫描接入 ============

    async def call_nmap_scan(self, task_id: str, target: str):
        """调用nmap扫描接口"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.TOOL_RUNNER_URL}/v1/penetration/scan/nmap",
                    headers={"X-API-Key": self.API_KEY},
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
        # 检查任务是否存在
        if not os.path.exists(f"runs/{task_id}"):
            return {
                "status": "failed",
                "task_id": task_id,
                "error": "任务不存在"
            }
        
        # 排队并发控制
        if len(self.running_tasks) >= self.MAX_CONCURRENT:
            await self.task_queue.put(task_id)
            return {
                "status": "queued", 
                "task_id": task_id,
                "position": self.task_queue.qsize(),
                "message": "任务已加入排队"
            }
        
        # 标记任务开始
        self.running_tasks[task_id] = "running"
        
        try:
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
                
                # 根据错误类型返回不同提示
                if scan_result["error"] == "timeout":
                    error_msg = "端口扫描超时，目标可能无响应"
                    allow_retry = True
                elif "connection" in error_msg.lower():
                    error_msg = "无法连接到目标，请检查网络"
                    allow_retry = True
                else:
                    allow_retry = False
                
                await self.update_task_status(task_id, {
                    "state": "failed" if not allow_retry else "partial",
                    "stage": 1,
                    "progress": 0,
                    "error": error_msg,
                    "message": f"端口扫描失败: {error_msg}",
                    "flags": {"allow_retry": allow_retry}
                })
                
                return {
                    "status": "failed",
                    "task_id": task_id,
                    "error": error_msg,
                    "allow_retry": allow_retry
                }
            
            # 保存结果到assets.json
            with open(f"runs/{task_id}/assets.json", "w", encoding="utf-8") as f:
                json.dump(scan_result, f, ensure_ascii=False, indent=2)
            
            # 统计端口数量
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
                "message": f"端口扫描完成，发现 {port_count} 个开放端口",
                "metrics": {"open_ports": port_count}
            }
            
        except Exception as e:
            error_msg = str(e)
            await self.update_task_status(task_id, {
                "state": "failed",
                "stage": 1,
                "progress": 0,
                "error": error_msg,
                "message": f"端口扫描失败: {error_msg}"
            })
            return {
                "status": "failed",
                "task_id": task_id,
                "error": error_msg,
                "allow_retry": True
            }
        finally:
            # 从运行中移除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            # 检查队列中是否有等待的任务
            if not self.task_queue.empty():
                next_task = await self.task_queue.get()
                self.running_tasks[next_task] = "running"

    # ============ 审批 ============

    async def approve_or_reject(self, task_id: str, req):
        """处理审批"""
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
            return {"status": "approved", "task_id": task_id, "message": "审批通过，任务继续"}
        else:
            await self.update_task_status(task_id, {
                "state": "rejected",
                "message": f"审批拒绝: {req.remark}"
            })
            return {"status": "rejected", "task_id": task_id, "message": "审批拒绝，任务终止"}


# 服务实例
task_service = TaskService()