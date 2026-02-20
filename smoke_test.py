import os
import json
import shutil
from pathlib import Path
# 假设你已经按照建议将 namp.py 修正为 nmap.py
from api.v1.Penetration.runner.base import BaseRunner
from api.v1.Penetration.runner.nmap import NmapRunner


def setup_test_env():
    """清理并准备测试环境"""
    test_dir = Path("runs/test_task_s3")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    print("--- 测试环境初始化完成 ---")


def test_base_infrastructure():
    """验证任务一：BaseRunner 基础设施"""
    print("\n[开始测试] 任务一：基础设施逻辑")
    task_id = "test_task_s3"
    runner = BaseRunner(task_id)

    # 1. 验证目录创建
    assert os.path.exists(f"runs/{task_id}/logs"), "错误：未创建 logs 目录"
    print("OK: 物理目录结构已建立")

    # 2. 验证初始状态落盘
    status_path = f"runs/{task_id}/status.json"
    assert os.path.exists(status_path), "错误：未创建初始 status.json"
    with open(status_path, "r", encoding="utf-8") as f:
        status = json.load(f)
        assert status["state"] == "init", "错误：初始状态不正确"
    print("OK: status.json 初始合同已落盘")


def test_stage1_nmap_integration():
    """验证任务二：NmapRunner 真实执行与解析"""
    print("\n[开始测试] 任务二：Stage 1 (Nmap) 集成逻辑")
    task_id = "test_task_s3"
    target = "127.0.0.1"
    runner = NmapRunner(task_id)

    # 执行扫描（模拟或真实，取决于环境）
    print(f"正在模拟/执行 Nmap 扫描目标: {target}...")
    runner.scan(target, ports="80,443")

    # 1. 验证资产文件落盘
    asset_path = f"runs/{task_id}/assets.json"
    assert os.path.exists(asset_path), "错误：Stage 1 未生成 assets.json"

    with open(asset_path, "r") as f:
        data = json.load(f)
        assert data["task_id"] == task_id, "错误：资产文件 task_id 匹配失败"
        assert "hosts" in data, "错误：资产文件缺少 hosts 字段"
    print("OK: assets.json 产物符合 Schema 要求")

    # 2. 验证日志追踪
    log_path = f"runs/{task_id}/logs/stage1_asset.log"
    assert os.path.exists(log_path), "错误：未生成 stage1_asset.log"
    print("OK: 工具执行日志已追踪")

    # 3. 验证状态机推进
    with open(f"runs/{task_id}/status.json", "r", encoding="utf-8") as f:
        status = json.load(f)
        assert status["percent"] >= 30, "错误：状态机进度未推进"
    print("OK: 状态机已更新至 Stage 1 完成态")


if __name__ == "__main__":
    try:
        setup_test_env()
        test_base_infrastructure()
        test_stage1_nmap_integration()
        print("\n🏆 [测试结论] S3 Tool-Runner 核心功能校验通过！")
    except Exception as e:
        print(f"\n❌ [测试失败] 发现回归问题: {str(e)}")
        exit(1)