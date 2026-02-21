import requests
import time
import json
import os
import sys
import io

# 强制设置控制台编码
if sys.platform == 'win32':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8020/v1"
API_KEY = "test-key"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def print_step(step, msg):
    print(f"\n[{step}] {msg}")
    print("-" * 40)

def test_all():
    print("=" * 50)
    print("一键自检脚本 (完整版)")
    print("=" * 50)
    
    # 1. 创建任务
    print_step("1/9", "创建任务")
    create_data = {
        "target": "127.0.0.1",
        "budget": {"timeout_seconds": 300}
    }
    r = requests.post(f"{BASE_URL}/task/create", headers=HEADERS, json=create_data)
    print(f"返回: {r.json()}")
    task_id = r.json().get("task_id")
    if not task_id:
        print("❌ 创建任务失败")
        return
    print(f"✅ 任务创建成功: {task_id}")
    
    # 2. 运行任务
    print_step("2/9", "运行任务")
    run_data = {"task_id": task_id}
    r = requests.post(f"{BASE_URL}/task/run", headers=HEADERS, json=run_data)
    print(f"返回: {r.json()}")
    
    # 3. 等待 Dify 执行（模拟）
    print_step("3/9", "等待 Dify 执行扫描")
    print("    (实际由 Dify 工作流调用 penetration 接口)")
    print("    生成 assets.json / http_fingerprints.json 等文件")
    time.sleep(2)
    
    # 4. 查状态 (运行后)
    print_step("4/9", "查状态 (运行后)")
    r = requests.get(f"{BASE_URL}/task/status", headers=HEADERS, params={"task_id": task_id})
    print(f"状态: {json.dumps(r.json(), indent=2, ensure_ascii=False)}")
    
    # 5. 指纹探测
    print_step("5/9", "指纹探测")
    r = requests.post(f"{BASE_URL}/penetration/probe/httpx", headers=HEADERS, params={"task_id": task_id})
    print(f"返回: {r.json()}")
    
    # 6. 查状态 (指纹探测后)
    print_step("6/9", "查状态 (指纹探测后)")
    r = requests.get(f"{BASE_URL}/task/status", headers=HEADERS, params={"task_id": task_id})
    status_data = r.json()
    print(f"状态: {json.dumps(status_data, indent=2, ensure_ascii=False)}")
    
    # 7. 查看生成的文件
    print_step("7/9", "查看生成的文件")
    runs_dir = f"runs/{task_id}"
    if os.path.exists(runs_dir):
        files = os.listdir(runs_dir)
        print(f"📁 runs/{task_id}/ 目录下的文件:")
        for f in files:
            file_path = f"{runs_dir}/{f}"
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"   - {f} ({size} bytes)")
                
                # 如果是json文件，显示前几行
                if f.endswith('.json'):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as jf:
                            content = json.load(jf)
                            preview = json.dumps(content, indent=2, ensure_ascii=False)
                            if len(preview) > 200:
                                preview = preview[:200] + "..."
                            print(f"     内容预览: {preview}")
                    except Exception as e:
                        print(f"     读取失败: {e}")
    else:
        print(f"❌ runs/{task_id}/ 目录不存在")
    
    # 8. 审批
    print_step("8/9", "审批任务")
    r = requests.post(
        f"{BASE_URL}/task/approve",
        headers=HEADERS,
        json={
            "task_id": task_id,
            "action": "approve",
            "approver": "殷瑞涵"
        }
    )
    print(f"✅ 审批结果: {r.json()}")
    
    # 9. 下载
    print_step("9/9", "下载产物")
    r = requests.get(
        f"{BASE_URL}/task/artifacts/download",
        headers=HEADERS,
        params={"task_id": task_id, "path": "report.md"}
    )
    if r.status_code == 200:
        filename = f"{task_id}_artifacts.zip"
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"✅ 下载成功: {filename}")
    else:
        print(f"⚠️ 下载失败: {r.status_code}")
    
    print("\n" + "=" * 50)
    print("✅ 一键自检完成！")
    print("=" * 50)

if __name__ == "__main__":
    test_all()