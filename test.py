import requests
import time
import json

BASE_URL = "http://localhost:8020/v1"  

def test_all():
    print("="*50)
    print("一键自检脚本")
    print("="*50)
    
    # 1. 创建任务
    print("\n[1/5] 创建任务...")
    r = requests.post(
        f"{BASE_URL}/tasks", 
        json={
            "target": "127.0.0.1",
            "budget": {"timeout_seconds": 300}
        }
    )
    print(f"返回状态码: {r.status_code}")
    print(f"返回内容: {r.text}")
    
    if r.status_code != 200:
        print("❌ 创建任务失败")
        return
        
    data = r.json()
    task_id = data.get("task_id")
    if not task_id:
        print("❌ 没有获取到task_id")
        return
    print(f"✅ 任务创建成功: {task_id}")
    
    # 2. 运行任务
    print("\n[2/5] 运行任务...")
    r = requests.post(f"{BASE_URL}/tasks/{task_id}/run")
    print(f"✅ 运行结果: {r.json()}")
    
    # 3. 轮询状态
    print("\n[3/5] 轮询状态...")
    for i in range(5):
        r = requests.get(f"{BASE_URL}/tasks/{task_id}")
        status = r.json()
        print(f"   第{i+1}次: stage={status.get('stage')}, progress={status.get('progress')}%")
        if status.get('stage') == 1 and status.get('progress') == 100:
            print("✅ 扫描完成！")
            break
        time.sleep(1)
    
    # 4. 审批（修复版）
    print("\n[4/5] 审批...")
    r = requests.post(
        f"{BASE_URL}/tasks/{task_id}/approve",
        json={
            "task_id": task_id,  # 加上这个！
            "action": "approve", 
            "approver": "test", 
            "remark": "通过"
        }
    )
    print(f"✅ 审批结果: {r.json()}")
    
    # 5. 下载
    print("\n[5/5] 下载...")
    r = requests.get(f"{BASE_URL}/tasks/{task_id}/download.zip")
    if r.status_code == 200:
        with open(f"{task_id}.zip", "wb") as f:
            f.write(r.content)
        print(f"✅ 下载成功: {task_id}.zip")
    else:
        print(f"⚠️ 下载失败: {r.status_code}")
    
    print("\n" + "="*50)
    print("✅ 一键自检完成！")
    print("="*50)

if __name__ == "__main__":
    test_all()