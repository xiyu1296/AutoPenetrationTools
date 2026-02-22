import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class NiktoRunner(BaseRunner):
    """独立 Nikto 服务器扫描执行器"""

    def run_scan(self, target_url: str) -> List[Dict[str, Any]]:
        if not target_url:
            return []

        self.write_log("tool_nikto", f"启动 Nikto 扫描，目标: {target_url}")

        script_path = os.path.abspath(os.path.join(os.getcwd(), "nikto", "program", "nikto.pl"))
        if not os.path.exists(script_path):
            self.write_log("tool_nikto", f"未找到脚本: {script_path}。请确认位于 nikto/program/ 目录下。")
            return []

        tmp_output = self.base_dir / "nikto_raw.json"

        # perl nikto.pl -h <url> -Format json -o <output>
        cmd = [
            "perl", script_path,
            "-h", target_url,
            "-Format", "json",
            "-o", str(tmp_output)
        ]

        self.run_tool(cmd, "tool_nikto")

        findings = []
        if tmp_output.exists():
            try:
                with open(tmp_output, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Nikto JSON 输出结构特殊，vulnerabilities 嵌套在数组内
                    if isinstance(data, list) and len(data) > 0:
                        vulns = data[0].get("vulnerabilities", [])
                        for item in vulns:
                            findings.append({
                                "id": item.get("id", ""),
                                "method": item.get("method", ""),
                                "url": item.get("url", ""),
                                "msg": item.get("msg", "")
                            })
            except Exception as e:
                self.write_log("tool_nikto", f"解析输出失败: {e}")

        self.save_artifact("nikto_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings