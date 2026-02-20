import os
import json
import shutil
import unittest
import zipfile
from pathlib import Path

# 导入业务 Runner 与 Service
from api.v1.Penetration.service import TaskService
from api.v1.Penetration.runner.nmap import NmapRunner
from api.v1.Penetration.runner.httpx import HttpxRunner
from api.v1.Penetration.runner.crawler import CrawlerRunner
from api.v1.Penetration.runner.candidate import CandidateRunner
from api.v1.Penetration.runner.validator import ValidatorRunner
from api.v1.Penetration.reporter import ReporterRunner


class FinalPipelineIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """初始化测试环境"""
        cls.task_id = "final_full_chain_v3"
        cls.target = "127.0.0.1"
        cls.base_dir = Path(f"runs/{cls.task_id}")
        if cls.base_dir.exists():
            shutil.rmtree(cls.base_dir)
        print(f"--- 开始全链路自动化测试 (Task ID: {cls.task_id}) ---")

    def test_01_environment_ready(self):
        """1. 检查物理环境与外部工具部署"""
        print("[Check] 正在验证工具部署...")
        required_tools = ["./pd-httpx.exe", "./katana.exe", "nmap", "curl"]
        for tool in required_tools:
            exists = os.path.exists(tool) or shutil.which(tool)
            self.assertTrue(exists, f"错误：关键工具缺失 -> {tool}")

    def test_02_execute_sequential_pipeline(self):
        """2. 顺序触发 Stage 1-6"""
        print("[Exec] 启动全链路流水线...")

        # 侦察与识别
        NmapRunner(self.task_id).scan(self.target, ports="8080")
        HttpxRunner(self.task_id).run_fingerprint()

        # 爬取与筛选
        CrawlerRunner(self.task_id).run_crawl()
        CandidateRunner(self.task_id).filter_candidates()

        # 验证与报告
        ValidatorRunner(self.task_id).verify()
        ReporterRunner(self.task_id).generate_final_package()

    def test_03_verify_evidence_store(self):
        """3. 验证证据仓库 (Evidence Store) 的 JSON 产物"""
        print("[Verify] 正在审计 JSON 证据链...")
        artifacts = [
            "assets.json", "http_fingerprints.json",
            "endpoints.json", "candidates.json", "findings.json"
        ]
        for art in artifacts:
            path = self.base_dir / art
            self.assertTrue(path.exists(), f"关键证据缺失: {art}")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.assertEqual(data.get("task_id"), self.task_id)

    def test_04_logic_accuracy_check(self):
        """4. 业务逻辑校验：回退机制与验证成功率"""
        print("[Verify] 正在校验 302 重定向与验证逻辑...")

        # 校验 Stage 4 候选点是否捕捉到 login.php
        with open(self.base_dir / "candidates.json", 'r', encoding='utf-8') as f:
            candidates = json.load(f).get("candidates", [])
            self.assertTrue(any("login.php" in c['url'] for c in candidates), "错误：未能捕获重定向目标 login.php")

        # 校验 Stage 5 验证证据是否真实有效
        with open(self.base_dir / "findings.json", 'r', encoding='utf-8') as f:
            findings = json.load(f).get("findings", [])
            self.assertTrue(any("200 OK" in f['evidence_data'] or "302" in f['evidence_data'] for f in findings),
                            "错误：验证阶段未采集到有效 HTTP 证据")

    def test_05_delivery_artifact_check(self):
        """5. 最终交付物审计 (Report & Zip)"""
        print("[Verify] 正在审计最终交付物...")

        # 检查 Markdown 报告内容
        report_path = self.base_dir / "report.md"
        self.assertTrue(report_path.exists())
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("# 自动化渗透测试报告", content)
            self.assertIn("login.php", content)

        # 检查压缩包是否包含所有必要文件
        zip_file = self.base_dir / f"artifacts_{self.task_id}.zip"
        self.assertTrue(zip_file.exists())
        with zipfile.ZipFile(zip_file, 'r') as z:
            namelist = z.namelist()
            self.assertIn("findings.json", namelist)
            self.assertIn("report.md", namelist)
            self.assertIn("logs/stage1_asset.log", namelist)

    def test_06_state_machine_final_status(self):
        """6. 验证状态机最终一致性"""
        print("[Verify] 检查任务最终状态...")
        status_path = self.base_dir / "status.json"
        with open(status_path, 'r', encoding='utf-8') as f:
            status = json.load(f)
            self.assertEqual(status.get("percent"), 100)
            self.assertEqual(status.get("stage"), "Stage6_Report")


if __name__ == "__main__":
    unittest.main()