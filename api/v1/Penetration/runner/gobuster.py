import os
import re
from typing import List, Dict, Any
from .base import BaseRunner


class GobusterRunner(BaseRunner):
    """独立 Gobuster 目录枚举执行器"""

    def run_scan(self, target_url: str, wordlist: str = "common.txt") -> List[Dict[str, Any]]:
        if not target_url:
            return []

        self.write_log("tool_gobuster", f"启动 Gobuster 目录扫描，目标: {target_url}")

        binary_path = os.path.abspath(os.path.join(os.getcwd(), "gobuster.exe"))
        binary = binary_path if os.path.exists(binary_path) else "gobuster"
        wordlist_path = os.path.abspath(os.path.join(os.getcwd(), wordlist))

        tmp_output = self.base_dir / "gobuster_raw.txt"

        # gobuster.exe dir -u <url> -w <wordlist> -o <output> -q -z
        # -q: quiet, -z: no progress
        cmd = [
            binary, "dir",
            "-u", target_url,
            "-w", wordlist_path,
            "-o", str(tmp_output),
            "-q", "-z"
        ]

        self.run_tool(cmd, "tool_gobuster")

        findings = []
        if tmp_output.exists():
            # 正则匹配形如: /admin (Status: 200) [Size: 1234]
            pattern = re.compile(r"^(.*?)\s+\(Status:\s+(\d+)\)\s+\[Size:\s+(\d+)\]")

            with open(tmp_output, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    match = pattern.search(line)
                    if match:
                        findings.append({
                            "path": match.group(1).strip(),
                            "status": int(match.group(2)),
                            "size": int(match.group(3))
                        })

        self.save_artifact("gobuster_findings.json", {"task_id": self.task_id, "findings": findings})
        return findings