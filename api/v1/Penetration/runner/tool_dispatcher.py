from api.v1.Penetration.runner.amass import AmassRunner
from api.v1.Penetration.runner.dnsx import DnsxRunner
from api.v1.Penetration.runner.gun import GauRunner
from api.v1.Penetration.runner.masscan import MasscanRunner
from api.v1.Penetration.runner.naabu import NaabuRunner
from api.v1.Penetration.runner.nuclei import NucleiRunner
from api.v1.Penetration.runner.oneforall import OneForAllRunner
from api.v1.Penetration.runner.paramspider import ParamSpiderRunner
from api.v1.Penetration.runner.shodan import ShodanRunner
from api.v1.Penetration.runner.sqlmap import SqlmapRunner
from api.v1.Penetration.runner.dirscan import DirScanRunner
from api.v1.Penetration.runner.hydra import HydraRunner
from api.v1.Penetration.runner.subfinder import SubfinderRunner
from api.v1.Penetration.runner.theharvester import TheHarvesterRunner
from api.v1.Penetration.runner.trufflehog import TrufflehogRunner
from api.v1.Penetration.runner.wafw00f import Wafw00fRunner
from api.v1.Penetration.runner.whatweb import WhatWebRunner


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

        elif tool_id == "subfinder":
            runner = SubfinderRunner(task_id)
            findings = runner.run_scan(target_domain=args.get("target_domain", ""))
            summary = f"Subfinder 枚举完成，发现 {len(findings)} 个子域名。"

        elif tool_id == "amass":
            runner = AmassRunner(task_id)
            findings = runner.run_scan(target_domain=args.get("target_domain", ""))
            summary = f"Amass 被动测绘完成，发现 {len(findings)} 个相关资产。"

        elif tool_id == "dnsx":
            runner = DnsxRunner(task_id)
            findings = runner.run_scan(subdomains=args.get("subdomains", []))
            summary = f"Dnsx 存活解析完成，确认存活 {len(findings)} 个记录。"

        elif tool_id == "oneforall":
            runner = OneForAllRunner(task_id)
            findings = runner.run_scan(target_domain=args.get("target_domain", ""))
            summary = f"OneForAll 扫描完成，发现 {len(findings)} 个子域名。"

        elif tool_id == "gau":
            runner = GauRunner(task_id)
            findings = runner.run_scan(target_domain=args.get("target_domain", ""))
            summary = f"Gau 历史 URL 提取完成，发现 {len(findings)} 条记录。"

        elif tool_id == "theharvester":
            runner = TheHarvesterRunner(task_id)
            res = runner.run_scan(
                target_domain=args.get("target_domain", ""),
                source=args.get("source", "all")
            )
            # 展平封装格式以符合 UnifiedToolResponse
            findings = [res]
            summary = f"theHarvester 收集完成，提取 {len(res.get('emails', []))} 个邮箱及 {len(res.get('hosts', []))} 个主机。"

        elif tool_id == "trufflehog":
            runner = TrufflehogRunner(task_id)
            findings = runner.run_scan(target_url=args.get("target_url", ""))
            summary = f"Trufflehog 扫描完成，发现 {len(findings)} 处代码凭证泄露。"

        elif tool_id == "shodan":
            runner = ShodanRunner(task_id)
            res = runner.run_scan(target_ip=args.get("target_ip", ""))
            findings = [res] if res else []
            summary = f"Shodan 检索完成，目标系统: {res.get('os', 'Unknown')}，开放端口: {res.get('ports', [])}。"

        elif tool_id == "masscan":
            runner = MasscanRunner(task_id)
            findings = runner.run_scan(
                target_ip=args.get("target_ip", ""),
                ports=args.get("ports", "1-65535"),
                rate=args.get("rate", 1000)
            )
            summary = f"Masscan 扫描完成，发现 {len(findings)} 个开放端口。"

        elif tool_id == "naabu":
            runner = NaabuRunner(task_id)
            findings = runner.run_scan(target=args.get("target", ""))
            summary = f"Naabu 扫描完成，确认 {len(findings)} 个存活端口。"

        elif tool_id == "whatweb":
            runner = WhatWebRunner(task_id)
            findings = runner.run_scan(target_url=args.get("target_url", ""))
            summary = f"WhatWeb 指纹识别完成，探测到 {len(findings[0].get('plugins', {})) if findings else 0} 项技术特征。"


        elif tool_id == "wafw00f":
            runner = Wafw00fRunner(task_id)
            findings = runner.run_scan(target_url=args.get("target_url", ""))

            # 提取检测到的 WAF 名称用于生成摘要
            detected_wafs = [f.get("firewall") for f in findings if f.get("detected")]
            waf_status = ", ".join(detected_wafs) if detected_wafs else "未检测到 WAF"

            summary = f"Wafw00f 探测完成，目标 WAF 状态: {waf_status}。"


        elif tool_id == "arjun":
            runner = ArjunRunner(task_id)
            findings = runner.run_scan(target_url=args.get("target_url", ""))
            summary = f"Arjun 参数爆破完成，发现 {len(findings)} 个隐藏参数。"

        elif tool_id == "paramspider":
            runner = ParamSpiderRunner(task_id)
            # ParamSpiderRunner 已重写为无需第三方库的原生代码
            findings = runner.run_scan(target_domain=args.get("target_domain", ""))
            summary = f"ParamSpider 运行完成，捕获 {len(findings)} 个带参 URL。"

        else:
            raise ValueError(f"未注册的 tool_id: {tool_id}")

        return {
            "tool_id": tool_id,
            "summary": summary,
            "findings": findings
        }