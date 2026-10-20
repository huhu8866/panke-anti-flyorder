#!/usr/bin/env python3
"""判客防飞单：输入线索 JSON，输出归属与风险等级。v1.0.0(内测基线)"""
import json
import sys
from datetime import datetime

RULES = {"report_valid_days": 7, "protect_days": 30, "followup_gap_days": 15}
HIGH, MID = {"F1", "F2", "F4", "F5", "F6"}, {"F3", "F7"}


def d(s):
    return datetime.strptime(s, "%Y-%m-%d")


def owner(recs, r=RULES):
    reports = [x for x in recs if x["type"] == "report" and x.get("approved")]
    first = min((x for x in recs if x["type"] == "visit"), key=lambda x: d(x["date"]), default=None)
    if reports:
        rp = min(reports, key=lambda x: d(x["date"]))
        if (d(first["date"]) - d(rp["date"])).days <= r["report_valid_days"]:
            return rp["sales"], "有效报备优先"
    if first:
        gap = (datetime.now() - d(first["date"])).days
        return first["sales"], "首访归属" if gap <= r["protect_days"] else "超保护期，可释放"
    return None, "证据不足"


def risks(recs, r=RULES):
    hits = []
    kinds = {x["type"] for x in recs}
    if "deal" in kinds and not any(x["type"] == "report" and x.get("approved") for x in recs):
        hits.append(("F1", "成交但无有效报备"))
    if any(x["type"] == "report" for x in recs) and any(
            x["type"] == "visit" and x.get("channel") == "natural" for x in recs):
        hits.append(("F2", "渠道报备后又出现自然到访成交"))
    if any(x.get("related") for x in recs):
        hits.append(("F4", "存在关联人登记记录"))
    if any(x.get("id_mismatch") for x in recs):
        hits.append(("F5", "报备信息与到访人不一致"))
    if any(x["type"] == "deal" and x.get("offsystem") for x in recs):
        hits.append(("F6", "房源不在系统/收款异常"))
    level = "高" if any(h[0] in HIGH for h in hits) else ("中" if hits else "低")
    return hits, level


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    who, why = owner(data["records"])
    hits, level = risks(data["records"])
    print(json.dumps({"归属": who, "依据": why, "风险等级": level, "命中规则": hits},
                     ensure_ascii=False, indent=2))
