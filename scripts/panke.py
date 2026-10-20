#!/usr/bin/env python3
"""判客防飞单：输入线索 JSON，输出归属与风险等级。v1.1.0(内测修复版)"""
import json
import sys
from datetime import datetime, timedelta

RULES = {"report_valid_days": 7, "protect_days": 30, "followup_gap_days": 15}
CHANNEL_TYPES = {"channel", "distributor", "agency"}
HIGH, MID = {"F1", "F2", "F4", "F5", "F6"}, {"F3", "F7"}
ACTIONS = {
    "F1": "要求补全报备链路，佣金暂缓结算",
    "F2": "核对报备手机号与到访登记，按渠道优先重新归属",
    "F3": "合并客户档案，锁定最早登记项目归属",
    "F4": "调取关系证明，合并档案并追溯原归属人",
    "F5": "核查渠道报备真实性，必要时终止渠道合作",
    "F6": "立即上报风控与财务，冻结佣金并审计",
    "F7": "保护期内成交不予认可，维持当前判定归属",
}


def d(s):
    return datetime.strptime(s, "%Y-%m-%d")


def resolve_today(recs, today=None):
    if today:
        return d(today)
    dates = [d(x["date"]) for x in recs if x.get("date")]
    return max(dates) if dates else datetime.now()


def owner(recs, today=None):
    """按 有效报备 → 首访 → 保护期 判定归属。"""
    today = resolve_today(recs, today)
    visits = sorted((x for x in recs if x["type"] == "visit"), key=lambda x: d(x["date"]))
    reports = sorted((x for x in recs if x["type"] == "report" and x.get("approved")),
                     key=lambda x: d(x["date"]))
    first = visits[0] if visits else None

    if reports:
        rp = reports[0]
        if first is None:
            return rp["sales"], "有效报备优先"
        delta = (d(first["date"]) - d(rp["date"])).days
        if 0 <= delta <= RULES["report_valid_days"]:
            return rp["sales"], "有效报备优先"

    if first:
        gap = (today - d(first["date"])).days
        if gap <= RULES["protect_days"]:
            return first["sales"], "首访归属"
        return None, "超保护期，可释放"

    return None, "证据不足"


def risks(recs, today=None, owner_sales=None):
    """扫描 F1-F7 飞单风险，返回 (命中列表, 等级)。"""
    resolve_today(recs, today)
    hits = []
    deals = [x for x in recs if x["type"] == "deal"]
    reports = [x for x in recs if x["type"] == "report" and x.get("approved")]
    visits = [x for x in recs if x["type"] == "visit"]

    if deals and not reports:
        hits.append(("F1", "成交但无有效报备"))

    if deals:
        for rp in reports:
            if rp.get("channel") in CHANNEL_TYPES:
                rp_date = d(rp["date"])
                if any(x.get("channel") == "natural" and d(x["date"]) > rp_date for x in visits):
                    hits.append(("F2", "渠道报备后由自然客成交"))
                    break

    projects = {x.get("project") for x in visits if x.get("project")}
    if len(projects) >= 2:
        hits.append(("F3", f"同一客户跨 {len(projects)} 个项目登记"))

    if any(x.get("related") for x in recs):
        hits.append(("F4", "存在关联人登记记录"))

    if any(x.get("id_mismatch") for x in recs):
        hits.append(("F5", "报备信息与到访人不一致"))

    if any(x["type"] == "deal" and x.get("offsystem") for x in deals):
        hits.append(("F6", "房源不在系统/收款异常"))

    if owner_sales and visits and deals:
        own_reports = [x for x in reports if x["sales"] == owner_sales]
        if own_reports:
            start = d(min(own_reports, key=lambda x: d(x["date"]))["date"])
        else:
            start = d(min(visits, key=lambda x: d(x["date"]))["date"])
        deadline = start + timedelta(days=RULES["protect_days"])
        for dl in deals:
            if dl.get("sales") and dl["sales"] != owner_sales and d(dl["date"]) <= deadline:
                hits.append(("F7", f"{dl['sales']} 在保护期内成交同一客户"))
                break

    if not recs or (not visits and not reports):
        level = "待复核"
    elif any(h[0] in HIGH for h in hits):
        level = "高"
    elif hits:
        level = "中"
    else:
        level = "低"
    return hits, level


def validate(recs):
    """输入自检：类型、日期、必填字段。返回错误列表。"""
    errs = []
    for i, x in enumerate(recs, 1):
        if x.get("type") not in {"visit", "report", "deal"}:
            errs.append(f"第 {i} 条：type 仅支持 visit/report/deal")
        try:
            d(x.get("date", ""))
        except (ValueError, TypeError):
            errs.append(f"第 {i} 条：date 需为 YYYY-MM-DD 格式")
        if x.get("type") in {"visit", "report"} and not x.get("sales"):
            errs.append(f"第 {i} 条：缺少 sales（接待/报备人）")
    return errs


def judge(data):
    recs = data.get("records", [])
    errs = validate(recs)
    if errs:
        return {"输入有误": errs, "提示": "请补全日期与接待人后重新提交，未做任何归属判定"}
    today = data.get("today")
    who, why = owner(recs, today)
    hits, level = risks(recs, today, who)
    return {
        "归属": who,
        "依据": why,
        "风险等级": level,
        "命中规则": [{"编号": c, "说明": desc, "处置": ACTIONS[c]} for c, desc in hits],
        "待办": "证据不足，建议人工复核" if level == "待复核" else "按命中规则执行处置",
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    path = sys.argv[1] if len(sys.argv) > 1 else "tests/demo.json"
    data = json.load(open(path, encoding="utf-8"))
    print(json.dumps(judge(data), ensure_ascii=False, indent=2))
