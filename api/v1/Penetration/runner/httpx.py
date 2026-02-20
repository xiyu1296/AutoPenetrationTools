# api/v1/Penetration/runner/httpx.py
import json
import os
from .base import BaseRunner


class HttpxRunner(BaseRunner):
    """Stage 2: 调用外部 pd-httpx 工具进行指纹识别"""

    def run_fingerprint(self):
        self.update_status({"stage": "Stage2_Fingerprint", "hint": "正在调用外部工具进行指纹嗅探", "percent": 45})

        # 加载资产
        asset_path = self.base_dir / "assets.json"
        if not asset_path.exists(): return {"fingerprints": []}
        with open(asset_path, "r", encoding="utf-8") as f:
            assets = json.load(f)

        targets = [f"{h['ip']}:{p['port']}" for h in assets.get("hosts", []) for p in h.get("ports", [])]
        if not targets: return {"fingerprints": []}

        # 使用相对路径或绝对路径调用，规避 Python 库冲突
        # 建议将 exe 放在项目根目录
        binary = "./pd-httpx.exe" if os.path.exists("./pd-httpx.exe") else "httpx"

        target_str = ",".join(targets)
        cmd = [binary, "-u", target_str, "-title", "-tech-detect", "-status-code", "-json", "-silent"]

        self.write_log("stage2_httpx", f"执行工具命令: {' '.join(cmd)}")
        output = self.run_tool(cmd, "stage2_httpx")

        fingerprints = []
        if output:
            for line in output.strip().split('\n'):
                try:
                    fingerprints.append(json.loads(line))
                except:
                    continue

        result = {"task_id": self.task_id, "total_found": len(fingerprints), "fingerprints": fingerprints}
        self.save_artifact("http_fingerprints.json", result)
        self.update_status({"percent": 55, "hint": f"发现 {len(fingerprints)} 个 Web 指纹"})
        return result