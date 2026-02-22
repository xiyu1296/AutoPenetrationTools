import json
import os
from typing import List, Dict, Any
from .base import BaseRunner


class TrufflehogRunner(BaseRunner):
    """独立 Trufflehog 敏感凭证扫描执行器"""

    def run_scan(self, target_url: str) -> List[Dict[str, Any]]:
        if not target_url:
            return []

        self.write_log("tool_trufflehog", f"启动 Trufflehog，目标仓库: {target_url}")

        binary_path = os.path.abspath(os.path.join(os.getcwd(), "trufflehog.exe"))
        binary = binary_path if os.path.exists(binary_path) else "trufflehog"

        # 构造命令: trufflehog git <url> --json
        cmd = [binary, "git", target_url, "--json"]

        output = self.run_tool(cmd, "tool_trufflehog")

        findings = []
        if output:
            # Trufflehog 输出为 JSONL 格式（每一行是一个 JSON 对象）
            for line in output.splitlines():
                if not line.strip() or not line.startswith("{"):
                    continue
                try:
                    data = json.loads(line.strip())
                    findings.append({
                        "detector_name": data.get("DetectorName", "Unknown"),
                        "decoder_name": data.get("DecoderName", ""),
                        "redacted_secret": data.get("Redacted", ""),
                        "file_path": data.get("SourceMetadata", {}).get("Data", {}).get("Git", {}).get("file", ""),
                        "commit": data.get("SourceMetadata", {}).get("Data", {}).get("Git", {}).get("commit", "")
                    })
                except Exception as e:
                    continue

        self.save_artifact("trufflehog_findings.json", {"task_id": self.task_id, "findings": findings})

        self.write_log("tool_trufflehog", f"扫描完成，发现 {len(findings)} 处疑似凭证泄露")
        return findings