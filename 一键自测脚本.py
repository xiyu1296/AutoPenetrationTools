import requests
import time

BASE_URL = "http://localhost:8020/v1"
API_KEY = "test-key"  # 可能是这个，也可能是别的值

def test_all():
    print("="*50)
    print("一键自检脚本")
    print("="*50)
    
    # 公共 headers
    headers = {"X-API-Key": API_KEY}
    
    # 1. 创建任务
    print("\n[1/5] 创建任务...")
    r = requests.post(
        f"{BASE_URL}/task/create",
        headers=headers,  # 加上这个
        json={
            "target": "127.0.0.1",
            "budget": {"timeout_seconds": 300}
        }
    )
    print(f"返回: {r.json()}")
    
    if r.status_code != 200:
        print("❌ 创建任务失败")
        return
        
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

if __name__ == "__main__":
    test_all()