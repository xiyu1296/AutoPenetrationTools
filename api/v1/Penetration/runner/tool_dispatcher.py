from api.v1.Penetration.runner.nuclei import NucleiRunner
from api.v1.Penetration.runner.sqlmap import SqlmapRunner
from api.v1.Penetration.runner.dirscan import DirScanRunner
from api.v1.Penetration.runner.hydra import HydraRunner

class ToolDispatcher:
    @staticmethod
    def execute(task_id: str, tool_id: str, args: dict) -> dict:
        findings = []
        summary = ""

        if tool_id == "nuclei":
            runner = NucleiRunner(task_id)
            findings = runner.run_scan(
                targets=args.get("targets", []),
                templates=args.get("templates", ["cves/", "vulnerabilities/"])
            )
            summary = f"Nuclei 扫描完成，检测到 {len(findings)} 个漏洞。"

        elif tool_id == "sqlmap":
            runner = SqlmapRunner(task_id)
            res = runner.run_injection_test(
                target_url=args.get("target_url", ""),
                risk_level=args.get("risk_level", 1)
            )
            findings = [res] if res.get("is_vulnerable") else []
            summary = f"SQLMap 测试完成，漏洞状态: {res.get('is_vulnerable')}。"

        elif tool_id == "dirscan":
            runner = DirScanRunner(task_id)
            findings = runner.run_scan(
                target_url=args.get("target_url", ""),
                extensions=args.get("extensions", "php,txt,zip"),
                wordlist_type=args.get("wordlist_type", "small")
            )
            summary = f"DirScan 完成，发现 {len(findings)} 个隐藏路径。"

        elif tool_id == "hydra":
            runner = HydraRunner(task_id)
            res = runner.run_bruteforce(
                target_ip=args.get("target_ip", ""),
                service=args.get("service", ""),
                port=args.get("port", 0)
            )
            findings = res.get("findings", [])
            summary = f"Hydra 爆破完成，破解状态: {res.get('is_cracked')}。"

        else:
            raise ValueError(f"未注册的 tool_id: {tool_id}")

        return {
            "tool_id": tool_id,
            "summary": summary,
            "findings": findings
        }