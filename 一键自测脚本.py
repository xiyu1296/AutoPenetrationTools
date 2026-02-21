import requests
import time
import json

BASE_URL = "http://localhost:8020/v1"
API_KEY = "test-key"

def test_all():
    print("="*50)
    print("一键自检脚本")
    print("="*50)
    
    headers = {"X-API-Key": API_KEY}
    
    # 1. 创建任务
    print("\n[1/5] 创建任务...")
    r = requests.post(
        f"{BASE_URL}/task/create",
        headers=headers,
        json={
            "target": "127.0.0.1",
            "budget": {"timeout_seconds": 300}
        }
    )
    print(f"返回: {r.json()}")
    task_id = r.json().get("task_id")
    print(f"✅ 任务创建成功: {task_id}")
    
    # 2. 运行任务
    print("\n[2/5] 运行任务...")
    r = requests.post(
        f"{BASE_URL}/task/run",
        headers=headers,
        json={"task_id": task_id}
    )
    print(f"✅ 运行结果: {r.json()}")
    
    # ===== 新增：模拟等待 Dify 执行 =====
    print("\n[2.5/5] 等待 Dify 执行扫描...")
    print("    (实际由 Dify 工作流调用 penetration 接口)")
    print("    生成 assets.json / http_fingerprints.json 等文件")
    time.sleep(2)  # 模拟等待
    # ====================================
    
    # 3. 查状态
    print("\n[3/5] 查状态...")
    r = requests.get(
        f"{BASE_URL}/task/status",
        headers=headers,
        params={"task_id": task_id}
    )
    print(f"✅ 状态: {r.json()}")
    
    # 4. 审批
    print("\n[4/5] 审批...")
    r = requests.post(
        f"{BASE_URL}/task/approve",
        headers=headers,
        json={
            "task_id": task_id,
            "action": "approve",
            "approver": "test"
        }
    )
    print(f"✅ 审批结果: {r.json()}")
    
    # 5. 下载
    print("\n[5/5] 下载...")
    r = requests.get(
        f"{BASE_URL}/task/artifacts/download",
        headers=headers,
        params={"task_id": task_id, "path": "report.md"}
    )
    if r.status_code == 200:
        with open(f"{task_id}.zip", "wb") as f:
            f.write(r.content)
        print(f"✅ 下载成功")
    else:
        print(f"⚠️ 下载失败: {r.status_code}")
    
    # ===== 新增：查看生成的文件 =====
    print("\n📁 查看 runs 目录：")
    import os
    if os.path.exists(f"runs/{task_id}"):
        files = os.listdir(f"runs/{task_id}")
        for f in files:
            print(f"   - {f}")
    # ================================

if __name__ == "__main__":
    test_all()