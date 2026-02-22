import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class XrayRunner(BaseRunner):
    """独立 xray 主动扫描执行器"""

    def run_scan(self, target_url: str) -> List[Dict[str, Any]]:
        if not target_url:
            return []

        self.write_log("tool_xray", f"启动 xray 主动扫描，目标: {target_url}")

        binary_path = os.path.abspath(os.path.join(os.getcwd(), "xray.exe"))
        binary = binary_path if os.path.exists(binary_path) else "xray"

        tmp_output = self.base_dir / "xray_raw.json"

        # xray.exe webscan --basic-crawler <url> --json-output <output>
        cmd = [
            binary,
            "webscan",
            "--basic-crawler", target_url,
            "--json-output", str(tmp_output)
        ]

        self.run_tool(cmd, "tool_xray")

        findings = []
        if tmp_output.exists():
            try:
                with open(tmp_output, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # xray 输出为包含漏洞信息的 JSON 数组
                    for item in data:
                        findings.append({
                            "plugin": item.get("plugin"),
                            "target": item.get("target", {}).get("url", ""),
                            "detail": item.get("detail", {})
                        })
            except Exception as e:
                self.write_log("tool_xray", f"解析输出失败: {e}")

        self.save_artifact("xray_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings