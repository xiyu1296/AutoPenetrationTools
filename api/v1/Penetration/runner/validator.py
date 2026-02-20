import json
import subprocess
import os
from .base import BaseRunner


class ValidatorRunner(BaseRunner):
    """
    Stage 5: 受控验证执行器 (基于 curl 的证据采集)
    """

    def verify(self):
        self.update_status({"stage": "Stage5_Verify", "hint": "执行受控验证并采集证据", "percent": 90})

        # 1. 加载 Stage 4 候选点
        candidate_path = self.base_dir / "candidates.json"
        if not candidate_path.exists(): return {"findings": []}

        with open(candidate_path, "r", encoding="utf-8") as f:
            candidates = json.load(f).get("candidates", [])

        findings = []
        for cand in candidates:
            url = cand.get("url")
            self.write_log("stage5_verify", f"正在验证高价值目标: {url}")

            # 2. 调用外部工具采集证据 (curl -I 获取 HTTP 首部)
            # 这种方式能够证明该路径真实存在且可访问
            cmd = ["curl", "-I", "-s", "--connect-timeout", "5", url]

            output = self.run_tool(cmd, "stage5_verify")

            if output and ("200 OK" in output or "302" in output):
                findings.append({
                    "url": url,
                    "vulnerability": "Potential Sensitive Interface",
                    "evidence_type": "HTTP_HEADER",
                    "evidence_data": output.strip().split('\n')[0],  # 仅保留首行状态码作为核心证据
                    "severity": "Medium" if "login" in url else "Low"
                })

        # 3. 产物保存
        result = {"task_id": self.task_id, "findings": findings}
        self.save_artifact("findings.json", result)

        self.update_status({
            "percent": 95,
            "hint": f"任务全链路已完成，发现 {len(findings)} 个有效风险点"
        })
        return result