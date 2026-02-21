import requests
import json
import time
from typing import Optional, Dict, Any

# 配置信息
WORKFLOW_ID = "f0fbd2cb-6b74-4e3c-b20f-9bcd106063b2"
API_KEY = "app-2u1fojUHcNAEnArkUa6hK7Sm"
API_BASE_URL = " https://baggiest-wade-untypically.ngrok-free.dev/v1"  #


def run_workflow(
        target: str,
        base_url: str,
        timeout_seconds: int = 900,
        rate_limit_rps: int = 1,
        response_mode: str = "streaming",
        wait_completion: bool = True
) -> Dict[str, Any]:
    """
    调用Dify工作流

    Args:
        target: 目标
        base_url: 基础URL
        timeout_seconds: 超时时间(秒) - 注意：这是顶层字段，不在budget里
        rate_limit_rps: 速率限制 - 注意：这是顶层字段，不在budget里
        response_mode: streaming 或 blocking
        wait_completion: 是否等待执行完成(仅streaming模式有效)

    Returns:
        工作流执行结果
    """

    # 构建请求体 - 关键修正：timeout_seconds和rate_limit_rps是顶层字段
    payload = {
        "inputs": {
            "target": target,
            "base_url": base_url,
            "timeout_seconds": timeout_seconds,  # 直接放在顶层，不在budget里
            "rate_limit_rps": rate_limit_rps  # 直接放在顶层，不在budget里
        },
        "response_mode": response_mode,
        "user": "test_user_001"  # 测试用户标识
    }

    # 构建请求头
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 发送请求
    url = f"{API_BASE_URL}/workflows/{WORKFLOW_ID}/run"
    print(f"发送请求到: {url}")
    print(f"请求参数: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=payload, stream=(response_mode == "streaming"))

        if response.status_code != 200:
            print(f"请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return {"error": response.text, "status_code": response.status_code}

        # 根据响应模式处理返回结果
        if response_mode == "blocking":
            return handle_blocking_response(response)
        else:
            return handle_streaming_response(response, wait_completion)

    except requests.exceptions.ConnectionError:
        print(f"连接错误: 无法连接到 {API_BASE_URL}")
        print("请确保Dify服务正在运行，且地址正确")
        return {"error": "connection_error"}
    except Exception as e:
        print(f"请求异常: {str(e)}")
        return {"error": str(e)}


def handle_blocking_response(response: requests.Response) -> Dict[str, Any]:
    """处理阻塞模式响应"""
    result = response.json()
    print("\n=== 阻塞模式执行结果 ===")
    print(f"Workflow执行ID: {result.get('workflow_run_id')}")
    print(f"任务ID: {result.get('task_id')}")

    data = result.get('data', {})
    print(f"状态: {data.get('status')}")

    # 如果有输出内容，打印出来
    outputs = data.get('outputs')
    if outputs:
        print(f"输出内容: {json.dumps(outputs, ensure_ascii=False, indent=2)}")

        # 特别提取你关心的字段
        if outputs.get('zip_path'):
            print(f"ZIP文件路径: {outputs['zip_path']}")
        if outputs.get('report_path'):
            print(f"报告文件路径: {outputs['report_path']}")

    if data.get('error'):
        print(f"错误信息: {data['error']}")

    if data.get('elapsed_time'):
        print(f"耗时: {data['elapsed_time']}秒")

    return result


def handle_streaming_response(response: requests.Response, wait_completion: bool) -> Dict[str, Any]:
    """处理流式模式响应"""
    print("\n=== 流式模式执行结果 ===")

    workflow_run_id = None
    task_id = None
    final_outputs = {}

    try:
        for line in response.iter_lines():
            if line and line.startswith(b'data: '):
                data_str = line[6:].decode('utf-8')  # 去掉 "data: " 前缀
                try:
                    data = json.loads(data_str)
                    event_type = data.get('event')

                    # 记录基本信息
                    if not workflow_run_id:
                        workflow_run_id = data.get('workflow_run_id')
                        task_id = data.get('task_id')
                        if workflow_run_id:
                            print(f"工作流运行ID: {workflow_run_id}")
                        if task_id:
                            print(f"任务ID: {task_id}")

                    # 根据不同事件类型处理
                    if event_type == 'workflow_started':
                        created_at = data.get('data', {}).get('created_at')
                        print(f"\n▶️ 工作流开始执行 - 时间: {created_at}")

                    elif event_type == 'node_started':
                        node_title = data.get('data', {}).get('title', '未知节点')
                        node_type = data.get('data', {}).get('node_type', '未知类型')
                        print(f"\n  ▶️ 节点开始执行: [{node_type}] {node_title}")

                    elif event_type == 'text_chunk':
                        text = data.get('data', {}).get('text', '')
                        if text:
                            print(text, end='', flush=True)

                    elif event_type == 'node_finished':
                        node_title = data.get('data', {}).get('title', '未知节点')
                        status = data.get('data', {}).get('status')
                        elapsed = data.get('data', {}).get('elapsed_time')

                        status_icon = "✅" if status == "succeeded" else "❌" if status == "failed" else "⏸️"
                        time_info = f" ({elapsed}秒)" if elapsed else ""
                        print(f"\n  {status_icon} 节点执行完成: {node_title} - 状态: {status}{time_info}")

                        # 如果是失败节点，显示错误
                        if status == "failed" and data.get('data', {}).get('error'):
                            print(f"     错误: {data['data']['error']}")

                    elif event_type == 'workflow_finished':
                        status = data.get('data', {}).get('status')
                        outputs = data.get('data', {}).get('outputs', {})
                        elapsed_time = data.get('data', {}).get('elapsed_time')
                        error = data.get('data', {}).get('error')

                        status_icon = "✅" if status == "succeeded" else "❌" if status == "failed" else "⏹️"
                        print(f"\n{status_icon} 工作流执行完成 - 状态: {status}")

                        if elapsed_time:
                            print(f"⏱️ 总耗时: {elapsed_time}秒")

                        if error:
                            print(f"❌ 错误: {error}")

                        if outputs:
                            print(f"\n📦 最终输出:")
                            print(json.dumps(outputs, ensure_ascii=False, indent=2))
                            final_outputs = outputs

                            # 特别提取你关心的字段
                            if outputs.get('zip_path'):
                                print(f"📎 ZIP文件: {outputs['zip_path']}")
                            if outputs.get('report_path'):
                                print(f"📄 报告文件: {outputs['report_path']}")

                        # 如果不等待完成，在这里返回
                        if not wait_completion:
                            return {
                                "workflow_run_id": workflow_run_id,
                                "task_id": task_id,
                                "status": status,
                                "outputs": outputs
                            }

                except json.JSONDecodeError as e:
                    print(f"\n⚠️ 解析数据失败: {e}")
                    print(f"原始数据: {data_str[:100]}...")  # 只显示前100个字符

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断了流式接收")
        if task_id:
            print(f"提示: 可以使用任务ID {task_id} 停止工作流")

    print("\n\n=== 流式接收完成 ===")
    return {
        "workflow_run_id": workflow_run_id,
        "task_id": task_id,
        "outputs": final_outputs
    }


def stop_workflow(task_id: str) -> bool:
    """
    停止正在执行的工作流

    Args:
        task_id: 任务ID

    Returns:
        是否成功停止
    """
    url = f"{API_BASE_URL}/workflows/tasks/{task_id}/stop"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    print(f"正在停止工作流: {task_id}")
    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 工作流 {task_id} 已停止")
        return True
    else:
        print(f"❌ 停止工作流失败: {response.status_code}")
        print(response.text)
        return False


def test_blocking_mode():
    """测试阻塞模式"""
    print("\n" + "=" * 60)
    print("测试用例1: 阻塞模式")
    print("=" * 60)

    result = run_workflow(
        target="test_target",
        base_url="http://example.com/api",
        timeout_seconds=600,  # 现在是顶层字段
        rate_limit_rps=2,  # 现在是顶层字段
        response_mode="blocking"
    )

    return result


def test_streaming_mode():
    """测试流式模式"""
    print("\n" + "=" * 60)
    print("测试用例2: 流式模式")
    print("=" * 60)

    result = run_workflow(
        target="test_target_2",
        base_url="http://test.com/api",
        timeout_seconds=300,  # 现在是顶层字段
        rate_limit_rps=5,  # 现在是顶层字段
        response_mode="streaming",
        wait_completion=True
    )

    return result


def simple_call_example():
    """简单的调用示例"""
    print("\n" + "=" * 60)
    print("简单调用示例")
    print("=" * 60)

    # 最简单的调用方式
    result = run_workflow(
        target="scan_target",
        base_url="https://api.example.com",
        timeout_seconds=900,  # 现在是顶层字段
        rate_limit_rps=1,  # 现在是顶层字段
        response_mode="blocking"  # 使用阻塞模式直接获取结果
    )

    # 检查结果
    if isinstance(result, dict):
        if result.get('data', {}).get('status') == 'succeeded':
            outputs = result.get('data', {}).get('outputs')
            if outputs:
                print("\n✅ 工作流执行成功!")
                print(f"任务ID: {result.get('task_id')}")
                if outputs.get('report_path'):
                    print(f"📄 报告路径: {outputs['report_path']}")
                if outputs.get('zip_path'):
                    print(f"📎 ZIP路径: {outputs['zip_path']}")
        elif result.get('error'):
            print(f"\n❌ 工作流执行失败: {result.get('error')}")

    return result


def main():
    """主测试函数"""

    # 测试阻塞模式
    result1 = test_blocking_mode()

    # 如果阻塞模式成功，等待一下再测试流式模式
    if result1 and not result1.get('error'):
        time.sleep(2)

        # 测试流式模式
        result2 = test_streaming_mode()

        # 如果获取到了task_id，可以测试停止功能（这里注释掉，根据需要启用）
        # if result2 and result2.get('task_id'):
        #     print("\n测试停止工作流...")
        #     time.sleep(1)
        #     stop_workflow(result2['task_id'])


if __name__ == "__main__":
    # 运行主测试函数
    main()

    # 或者只运行简单调用示例
    # simple_call_example()