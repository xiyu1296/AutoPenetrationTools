import json
import re
from .base import BaseRunner


class CandidateRunner(BaseRunner):
    """Stage 4: 精准候选点筛选器"""

    def filter_candidates(self):
        self.update_status({"stage": "Stage4_Candidate", "hint": "锁定高价值攻击路径", "percent": 80})

        endpoint_path = self.base_dir / "endpoints.json"
        if not endpoint_path.exists(): return {"candidates": []}

        with open(endpoint_path, "r", encoding="utf-8") as f:
            endpoints = json.load(f).get("endpoints", [])

        # 风险关键词
        risk_patterns = [r"login", r"admin", r"config", r"api", r"php"]
        candidates = []
        seen = set()

        for ep in endpoints:
            url = ep.get("request", {}).get("url")
            if not url or url in seen: continue

            # 检查是否匹配风险模式
            reason = "Base target"
            is_match = False
            for p in risk_patterns:
                if re.search(p, url, re.I):
                    reason = f"Matched risk pattern: {p}"
                    is_match = True
                    break

            # 录入规则：匹配风险模式或作为保底
            if is_match or len(candidates) < 3:
                candidates.append({
                    "url": url,
                    "reason": reason,
                    "method": ep.get("request", {}).get("method", "GET")
                })
                seen.add(url)

        self.save_artifact("candidates.json", {"task_id": self.task_id, "candidates": candidates})
        self.write_log("stage4_candidate", f"开始筛选流程，输入端点数: {len(endpoints)}")
        self.update_status({"percent": 85, "hint": f"锁定 {len(candidates)} 个高价值候选点"})