import json
from typing import List, Dict, Any
from .base import BaseRunner


class Wafw00fRunner(BaseRunner):
    """独立 Wafw00f WAF 探测执行器"""

    def run_scan(self, target_url: str) -> List[Dict[str, Any]]:
        if not target_url:
            return []

        self.write_log("tool_wafw00f", f"启动 Wafw00f 探测，目标: {target_url}")

        # wafw00f 支持根据文件后缀自动判断输出格式
        tmp_output = self.base_dir / "wafw00f_raw.json"

        # 构造命令: wafw00f <url> -o output.json
        cmd = [
            "wafw00f",
            target_url,
            "-o", str(tmp_output)
        ]

        self.run_tool(cmd, "tool_wafw00f")

        findings = []
        if tmp_output.exists():
            try:
                with open(tmp_output, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # wafw00f 的 JSON 输出通常是一个列表
                    if isinstance(data, list):
                        for item in data:
                            findings.append({
                                "url": item.get("url"),
                                "detected": item.get("detected", False),
                                "firewall": item.get("firewall", "None"),
                                "manufacturer": item.get("manufacturer", "Unknown")
                            })
            except Exception as e:
                self.write_log("tool_wafw00f", f"解析 JSON 输出失败: {e}")

        self.save_artifact("wafw00f_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings