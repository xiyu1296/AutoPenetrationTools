import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class TheHarvesterRunner(BaseRunner):
    """独立 theHarvester 执行器"""

    def run_scan(self, target_domain: str, source: str = "all") -> Dict[str, Any]:
        if not target_domain:
            return {"emails": [], "hosts": [], "ips": []}

        self.write_log("tool_theharvester", f"启动 theHarvester，目标: {target_domain}, 数据源: {source}")

        script_path = os.path.abspath(os.path.join(os.getcwd(), "theHarvester", "theHarvester.py"))
        if not os.path.exists(script_path):
            self.write_log("tool_theharvester", f"未找到脚本: {script_path}")
            return {"emails": [], "hosts": [], "ips": []}

        # theHarvester 会自动在指定路径后追加 .json 和 .xml 后缀
        tmp_output_base = self.base_dir / "harvester_raw"
        json_output = self.base_dir / "harvester_raw.json"

        # 构造命令: python theHarvester.py -d example.com -b all -f output_base
        cmd = [
            "python", script_path,
            "-d", target_domain,
            "-b", source,
            "-f", str(tmp_output_base)
        ]

        self.run_tool(cmd, "tool_theharvester")

        findings = {"emails": [], "hosts": [], "ips": []}
        if json_output.exists():
            try:
                with open(json_output, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    findings["emails"] = data.get("emails", [])
                    findings["hosts"] = data.get("hosts", [])
                    findings["ips"] = data.get("ips", [])
            except Exception as e:
                self.write_log("tool_theharvester", f"解析输出失败: {e}")

        self.save_artifact("theharvester_findings.json", {"task_id": self.task_id, "findings": [findings]})
        return findings