#!/usr/bin/env python3
"""技能内测运行器：对 panke.py 跑全部用例，输出通过率与失败明细。"""
import importlib.util
import inspect
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("panke", ROOT / "scripts" / "panke.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BASIS = {
    "有效报备优先": "report",
    "报备优先": "report",
    "首访归属": "first_visit",
    "超保护期，可释放": "expired",
    "证据不足": "insufficient",
}
OWNER_PARAMS = inspect.signature(mod.owner).parameters
RISK_PARAMS = inspect.signature(mod.risks).parameters


def call_owner(recs, today):
    if "today" in OWNER_PARAMS:
        return mod.owner(recs, today=today)
    return mod.owner(recs)


def call_risks(recs, today, who):
    if "today" in RISK_PARAMS:
        if "owner_sales" in RISK_PARAMS:
            return mod.risks(recs, today=today, owner_sales=who)
        return mod.risks(recs, today=today)
    return mod.risks(recs)


def main():
    data = json.load(open(ROOT / "tests" / "cases.json", encoding="utf-8"))
    total = passed = 0
    failures = []
    for c in data["cases"]:
        total += 1
        exp = c["expect"]
        try:
            who, why = call_owner(c["records"], c["today"])
            hits, level = call_risks(c["records"], c["today"], who)
            got = {
                "owner": who,
                "basis": BASIS.get(why, why),
                "level": level,
                "hits": [h[0] for h in hits],
            }
        except Exception as e:
            got = {"error": f"{type(e).__name__}: {e}"}

        ok = (
            "error" not in got
            and got["owner"] == exp["owner"]
            and got["basis"] == exp["basis"]
            and got["level"] == exp["level"]
            and all(h in got["hits"] for h in exp.get("hits", []))
        )
        if ok:
            passed += 1
            print(f"[PASS] {c['id']} - {c['desc']}")
        else:
            print(f"[FAIL] {c['id']} - {c['desc']}")
            print(f"       期望: {json.dumps(exp, ensure_ascii=False)}")
            print(f"       实际: {json.dumps(got, ensure_ascii=False)}")
            failures.append(c["id"])

    rate = passed / total if total else 0
    print(f"\n通过率: {passed}/{total} ({rate:.0%})")
    if failures:
        print("失败用例: " + ", ".join(failures))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
