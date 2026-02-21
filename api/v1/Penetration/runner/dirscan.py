# api/v1/Penetration/runner/dirscan.py
import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class DirScanRunner(BaseRunner):
    """独立 FFUF 目录扫描工具执行器 (集成 SecLists)"""

    def run_scan(self, target_url: str, extensions: str, wordlist_type: str) -> List[dict]:
        if not target_url:
            return []

        self.write_log("tool_dirscan", f"接收到目录爆破请求，目标: {target_url}，字典规模: {wordlist_type}")

        # 1. 字典路径映射 (基于项目根目录下的 SecLists)
        wordlist_map = {
            "small": "SecLists/Discovery/Web-Content/raft-small-directories.txt",
            "medium": "SecLists/Discovery/Web-Content/raft-medium-directories.txt",
            "large": "SecLists/Discovery/Web-Content/raft-large-directories.txt",
            "api": "SecLists/Discovery/Web-Content/api/api-endpoints.txt"
        }

        rel_path = wordlist_map.get(wordlist_type.lower(), wordlist_map["small"])
        wordlist_path = os.path.abspath(os.path.join(os.getcwd(), rel_path))

        if not os.path.exists(wordlist_path):
            self.write_log("tool_dirscan", f"字典文件缺失: {wordlist_path}。请确认已在项目根目录拉取 SecLists。")
            return []

        # 2. 工具路径适配
        binary_path = os.path.abspath(os.path.join(os.getcwd(), "ffuf.exe"))
        binary = binary_path if os.path.exists(binary_path) else "ffuf"

        target_url = target_url.rstrip("/")
        fuzz_url = f"{target_url}/FUZZ"
        tmp_output = self.base_dir / "ffuf_raw.json"

        # 3. 构造外部命令
        cmd = [
            binary,
            "-u", fuzz_url,
            "-w", wordlist_path,
            "-e", f".{extensions.replace(',', ',.')}",
            "-mc", "200,301,302,403",
            "-t", "50",  # 增加线程数以应对大字典
            "-o", str(tmp_output),
            "-of", "json",
            "-s"
        ]

        self.write_log("tool_dirscan", f"执行命令: {' '.join(cmd)}")
        self.run_tool(cmd, "tool_dirscan")

        # 4. 结果解析
        findings = []
        if tmp_output.exists():
            try:
                with open(tmp_output, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results = data.get("results", [])
                    for res in results:
                        findings.append({
                            "url": res.get("url"),
                            "status": res.get("status"),
                            "length": res.get("length"),
                            "title": ""
                        })
            except Exception as e:
                self.write_log("tool_dirscan", f"解析 FFUF 结果失败: {str(e)}")

        self.save_artifact("dirscan_findings.json", {"task_id": self.task_id, "findings": findings})
        self.write_log("tool_dirscan", f"扫描完成，发现 {len(findings)} 个路径")
        return findings