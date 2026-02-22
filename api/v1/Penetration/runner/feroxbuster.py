import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class FeroxbusterRunner(BaseRunner):
    """独立 Feroxbuster 递归目录发现执行器"""

    def run_scan(self, target_url: str, wordlist: str = "common.txt") -> List[Dict[str, Any]]:
        if not target_url:
            return []

        self.write_log("tool_feroxbuster", f"启动 Feroxbuster，目标: {target_url}")

        binary_path = os.path.abspath(os.path.join(os.getcwd(), "feroxbuster.exe"))
        binary = binary_path if os.path.exists(binary_path) else "feroxbuster"
        wordlist_path = os.path.abspath(os.path.join(os.getcwd(), wordlist))

        tmp_output = self.base_dir / "feroxbuster_raw.jsonl"

        # feroxbuster.exe -u <url> -w <wordlist> --json -o <output> --silent
        cmd = [
            binary,
            "-u", target_url,
            "-w", wordlist_path,
            "--json",
            "-o", str(tmp_output),
            "--silent"
        ]

        self.run_tool(cmd, "tool_feroxbuster")

        findings = []
        if tmp_output.exists():
            with open(tmp_output, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        # 仅提取响应类型的数据
                        if data.get("type") == "response":
                            findings.append({
                                "url": data.get("url"),
                                "status": data.get("status"),
                                "content_length": data.get("content_length"),
                                "line_count": data.get("line_count"),
                                "word_count": data.get("word_count")
                            })
                    except Exception:
                        continue

        self.save_artifact("feroxbuster_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings