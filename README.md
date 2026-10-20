# Lead Attribution & Anti-Fly-Order Assistant (Real Estate)

An agent skill (SKILL.md format) for real-estate sales-floor **lead attribution**
and **fly-order (commission-diversion) risk detection**. For AI agents (Claude
Skills / WorkBuddy / compatible runtimes).

## What it does
- Decides **whose client is this** when two agents claim the same lead.
- Detects **fly orders** (commission diverted off the books) with a 7-rule scan
  (F1–F7), each weighted high/medium.
- Outputs a fixed four-section verdict: ownership + protection days, risk list,
  evidence chain (chronological), and recommended action (freeze commission /
  retro-register / arbitrate / escalate to risk control).

## Decision logic
1. **Identity normalization**: same phone / same ID / related-party group = one
   client; related-party hits take the earliest registration record.
2. **Ownership priority**: valid registration → first-visit agent → within-
   protection re-visit → released to public pool.
3. **Fly-order scan**: F1 no-registration deal (high) / F2 channel conflict
   (high) / F3 cross-project collision (mid) / F4 related-party evasion (high) /
   F5 distributor wash (high) / F6 off-book deal (high) / F7 in-protection grab
   (mid).
4. **Verdict**: ≥1 high → high risk; only mid → mid; none → low; insufficient
   evidence → manual review (never fabricate).

## Quick start
```bash
python scripts/panke.py            # runs bundled tests/demo.json, cases.json, dirty.json
# configurable thresholds live at the top of scripts/panke.py under RULES
#   report_valid_days=7  protect_days=30  followup_gap_days=15  related_match=True
```

## Files
- `SKILL.md` — trigger, inputs, decision flow, output format, hard constraints.
- `scripts/panke.py` — deterministic engine + `RULES` config.
- `references/rules.md` — parameter table + attribution priority + F1–F7 table.
- `references/risk-cases.md` — 6 annotated fly-order case studies.
- `tests/` — demo / cases / dirty-input fixtures + runner.

## Compliance
Judge only on user-provided facts; insufficient evidence → "manual review".
Commission freezes / penalties are recommendations only, not a substitute for
company policy or law. Sensitive PII (phone/ID) must be collected and stored per
applicable data-protection law.

## Pricing
List at **$1 per arbitration/report** (or accept the marketplace's creator reward
points). Enterprise SaaS / per-project customization is a separate higher-tier
offer.

## License
MIT (code) / CC BY-NC 4.0 (rules & cases text).

## Hire me
Custom deployment, parameter tuning per agency policy, and API integration:
chenjianhu@agent.qq.com
