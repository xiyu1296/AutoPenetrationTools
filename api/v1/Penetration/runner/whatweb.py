import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class WhatWebRunner(BaseRunner):
    """独立 whatweb 指纹识别执行器"""

    def run_scan(self, target_url: str) -> List[Dict[str, Any]]:
        if not target_url:
            return []

        self.write_log("tool_whatweb", f"启动 whatweb，目标: {target_url}")

        script_path = os.path.abspath(os.path.join(os.getcwd(), "whatweb", "whatweb"))
        if not os.path.exists(script_path):
            self.write_log("tool_whatweb", f"未找到脚本: {script_path}")
            return []

        tmp_output = self.base_dir / "whatweb_raw.json"

        # 构造命令: ruby whatweb/whatweb <url> --log-json output.json
        cmd = [
            "ruby", script_path,
            target_url,
            "--log-json", str(tmp_output)
        ]

        self.run_tool(cmd, "tool_whatweb")

        findings = []
        if tmp_output.exists():
            try:
                with open(tmp_output, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        plugins = item.get("plugins", {})
                        # 展平结构，提取核心指纹 (CMS, Web Server, Framework)
                        detected_plugins = {k: v.get("version", [""])[0] for k, v in plugins.items()}

                        findings.append({
                            "target": item.get("target"),
                            "http_status": item.get("http_status"),
                            "plugins": detected_plugins
                        })
            except Exception as e:
                self.write_log("tool_whatweb", f"解析输出失败: {e}")

        self.save_artifact("whatweb_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings