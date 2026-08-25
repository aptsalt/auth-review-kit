#!/usr/bin/env python3
"""
render_status.py — turn config/repos.json into the coverage index.

Outputs:
  <workspace>/review-status.md    plain markdown, greppable, diffable in a PR
  <workspace>/review-status.html  dashboard for sharing with people who won't read markdown

The point of this file is honesty about coverage: what has been reviewed, what has not, what is
corroborated by telemetry, and — most importantly — what is invisible. A green board that hides
blind repos is worse than no board.

Usage:
  python scripts/render_status.py
  python scripts/render_status.py --repos config/repos.json --out ../review-workspace
"""

import argparse
import json
from datetime import date
from pathlib import Path

SEV = ["critical", "high", "medium", "low"]
VERDICTS = ["observed", "consistent", "no_signal", "blind", "unobservable"]


def load(p: Path):
    if not p.exists():
        raise SystemExit(f"{p} not found. Copy config/repos.example.json and onboard a repo first.")
    data = json.loads(p.read_text(encoding="utf-8"))
    return data.get("profile", "unknown"), data.get("repos", []), data.get("correlation", {})


def state_of(r):
    """A repo is one of: reviewed / partial / queued. Kept deliberately coarse."""
    if not r.get("reviewed"):
        return "queued"
    ran = len(r.get("dimensions_run") or [])
    planned = len(r.get("dimensions_planned") or []) or ran
    return "reviewed" if ran >= planned and ran > 0 else "partial"


def totals(repos):
    t = {"repos": len(repos), "reviewed": 0, "partial": 0, "queued": 0,
         "gaps": 0, "mapped": 0, "blind": 0, "unmapped": 0}
    t.update({s: 0 for s in SEV})
    t.update({v: 0 for v in VERDICTS})
    for r in repos:
        t[state_of(r)] += 1
        t["gaps"] += r.get("evidence_gaps", 0) or 0
        t[(r.get("dynatrace") or {}).get("status", "unmapped")] += 1
        for s in SEV:
            t[s] += (r.get("findings") or {}).get(s, 0) or 0
        for v in VERDICTS:
            t[v] += (r.get("verdicts") or {}).get(v, 0) or 0
    return t


def md(profile, repos, corr, t):
    L = []
    A = L.append
    A("# Review coverage index\n")
    A(f"> Profile `{profile}` · generated {date.today().isoformat()}")
    if corr.get("last_run"):
        A(f"> Last correlation run: {corr['last_run']} (window {corr.get('window', 'unknown')})")
    A("")
    A(f"**{t['reviewed']} reviewed · {t['partial']} partial · {t['queued']} queued** "
      f"of {t['repos']} repos · {t['gaps']} open evidence gaps\n")

    A("## Findings\n")
    A("| Critical | High | Medium | Low |")
    A("|---|---|---|---|")
    A(f"| {t['critical']} | {t['high']} | {t['medium']} | {t['low']} |\n")

    A("## Observability\n")
    A(f"`{t['mapped']}` mapped · `{t['blind']}` blind · `{t['unmapped']}` unmapped\n")
    if t["unmapped"]:
        A(f"> {t['unmapped']} repo(s) still unmapped. Correlation cannot produce a meaningful "
          f"verdict for these — resolve to `mapped` or `blind` before the next correlation run.\n")
    if t["blind"]:
        A(f"> {t['blind']} repo(s) are blind. Absence of telemetry there is not evidence of health.\n")

    if any(t[v] for v in VERDICTS):
        A("## Corroboration\n")
        A("| Observed | Consistent | No signal | Blind | Unobservable |")
        A("|---|---|---|---|---|")
        A(f"| {t['observed']} | {t['consistent']} | {t['no_signal']} | {t['blind']} | {t['unobservable']} |\n")

    A("## Repos\n")
    A("| Repo | Tier | Kind | State | Reviewed | Dynatrace | C | H | M | L | Gaps |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(repos, key=lambda x: (state_of(x) != "queued", x.get("name", ""))):
        f = r.get("findings") or {}
        dt = (r.get("dynatrace") or {})
        ent = dt.get("entity") or dt.get("status", "unmapped")
        A(f"| `{r.get('name','?')}` | {r.get('tier','-')} | {r.get('kind','-')} | "
          f"{state_of(r)} | {r.get('reviewed') or '—'} | {ent} | "
          f"{f.get('critical',0)} | {f.get('high',0)} | {f.get('medium',0)} | {f.get('low',0)} | "
          f"{r.get('evidence_gaps',0)} |")
    A("")

    queued = [r for r in repos if state_of(r) == "queued"]
    if queued:
        A("## Not yet reviewed\n")
        A("Absence of findings for these is not a pass — they have not been looked at.\n")
        for r in queued:
            A(f"- `{r['name']}` — {r.get('kind','?')}, {r.get('tier','?')}"
              + (f" · {r['notes']}" if r.get("notes") else ""))
        A("")
    return "\n".join(L)


CSS = """
:root{--bg:#F2F4F7;--sf:#fff;--sf2:#E9EDF3;--ink:#131A24;--ink2:#48566D;--ink3:#6F7D94;
--line:#D4DBE5;--ac:#1B4F9C;--acs:#E3ECFA;--ok:#136B41;--oks:#DEF0E6;--wn:#8A5D00;--wns:#F8EBD2;
--bd:#A81F18;--bds:#FAE3E1}
@media(prefers-color-scheme:dark){:root{--bg:#0E141C;--sf:#151E29;--sf2:#1C2734;--ink:#E8EDF4;
--ink2:#AAB7C9;--ink3:#7E8DA4;--line:#2A3746;--ac:#79ADFF;--acs:#16263E;--ok:#5CCB90;--oks:#12291F;
--wn:#E6B44A;--wns:#2B2415;--bd:#FF847B;--bds:#2E1A19}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif;
font-size:15px;line-height:1.6}
.w{max-width:1200px;margin:0 auto;padding:34px 22px 70px}
h1{font-family:"IBM Plex Serif",Georgia,serif;font-size:30px;margin:0 0 8px;letter-spacing:-.01em}
h2{font-family:"IBM Plex Serif",Georgia,serif;font-size:18px;margin:34px 0 12px;
padding-bottom:9px;border-bottom:1px solid var(--line)}
.sub{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.06em;color:var(--ink3);
text-transform:uppercase;margin-bottom:26px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:10px}
.c{background:var(--sf);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.c b{display:block;font-family:"IBM Plex Mono",monospace;font-size:26px;font-variant-numeric:tabular-nums;
line-height:1.15;margin-bottom:3px}
.c span{font-family:"IBM Plex Mono",monospace;font-size:9.5px;letter-spacing:.12em;
text-transform:uppercase;color:var(--ink3)}
.c.crit b{color:var(--bd)}.c.high b{color:var(--wn)}.c.ok b{color:var(--ok)}.c.ac b{color:var(--ac)}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--sf)}
table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:760px}
th{text-align:left;font-family:"IBM Plex Mono",monospace;font-size:9.5px;letter-spacing:.11em;
text-transform:uppercase;color:var(--ink3);font-weight:500;padding:9px 13px;
border-bottom:1px solid var(--line);background:var(--sf2);white-space:nowrap}
td{padding:9px 13px;border-bottom:1px solid var(--line);color:var(--ink2);
font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--sf2)}
td.n{font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--ink)}
.p{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:9.5px;letter-spacing:.05em;
text-transform:uppercase;padding:2px 8px;border-radius:20px;border:1px solid;white-space:nowrap}
.p.reviewed{color:var(--ok);background:var(--oks);border-color:var(--ok)}
.p.partial{color:var(--wn);background:var(--wns);border-color:var(--wn)}
.p.queued{color:var(--ink3);background:var(--sf2);border-color:var(--line)}
.p.blind{color:var(--bd);background:var(--bds);border-color:var(--bd)}
.p.unmapped{color:var(--wn);background:var(--wns);border-color:var(--wn)}
.p.mapped{color:var(--ac);background:var(--acs);border-color:var(--ac)}
.note{border-left:3px solid var(--wn);background:var(--wns);border-radius:0 8px 8px 0;
padding:12px 16px;margin:14px 0;font-size:14px;color:var(--ink2)}
.note.bad{border-left-color:var(--bd);background:var(--bds)}
.z{color:var(--ink3)}
"""


def html(profile, repos, corr, t):
    def card(v, label, cls=""):
        return f'<div class="c {cls}"><b>{v}</b><span>{label}</span></div>'

    rows = []
    for r in sorted(repos, key=lambda x: (state_of(x) != "queued", x.get("name", ""))):
        f = r.get("findings") or {}
        dt = r.get("dynatrace") or {}
        status = dt.get("status", "unmapped")
        ent = dt.get("entity") or status
        st = state_of(r)

        def num(v):
            return f'<td class="n">{v}</td>' if v else '<td class="n z">0</td>'
        rows.append(
            f'<tr><td class="n">{r.get("name","?")}</td>'
            f'<td>{r.get("tier","-")}</td><td>{r.get("kind","-")}</td>'
            f'<td><span class="p {st}">{st}</span></td>'
            f'<td>{r.get("reviewed") or "&mdash;"}</td>'
            f'<td><span class="p {status}">{ent}</span></td>'
            + num(f.get("critical", 0)) + num(f.get("high", 0))
            + num(f.get("medium", 0)) + num(f.get("low", 0))
            + num(r.get("evidence_gaps", 0)) + "</tr>")

    notes = ""
    if t["unmapped"]:
        notes += (f'<div class="note">{t["unmapped"]} repo(s) are still <b>unmapped</b> in Dynatrace. '
                  f'Correlation cannot produce a meaningful verdict for these — resolve each to '
                  f'<code>mapped</code> or <code>blind</code> before the next correlation run.</div>')
    if t["blind"]:
        notes += (f'<div class="note bad">{t["blind"]} repo(s) are <b>blind</b>. '
                  f'Absence of telemetry there is not evidence of health, and no finding in those '
                  f'repos may be downgraded for lack of production signal.</div>')
    if t["queued"]:
        notes += (f'<div class="note">{t["queued"]} repo(s) are <b>not yet reviewed</b>. '
                  f'Absence of findings for these is not a pass.</div>')

    corro = ""
    if any(t[v] for v in VERDICTS):
        corro = ("<h2>Corroboration against production</h2><div class='cards'>"
                 + card(t["observed"], "observed", "ok") + card(t["consistent"], "consistent")
                 + card(t["no_signal"], "no signal") + card(t["blind"], "blind", "crit")
                 + card(t["unobservable"], "unobservable") + "</div>")

    sub = f"profile {profile} &middot; generated {date.today().isoformat()}"
    if corr.get("last_run"):
        sub += f" &middot; last correlation {corr['last_run']}"

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Review Coverage</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@600&display=swap">
<style>{CSS}</style></head><body><div class="w">
<h1>Review coverage index</h1>
<div class="sub">{sub}</div>

<div class="cards">
{card(t['repos'], 'repos')}{card(t['reviewed'], 'reviewed', 'ok')}
{card(t['partial'], 'partial')}{card(t['queued'], 'queued')}
{card(t['gaps'], 'evidence gaps', 'ac')}
</div>

<h2>Findings</h2>
<div class="cards">
{card(t['critical'], 'critical', 'crit')}{card(t['high'], 'high', 'high')}
{card(t['medium'], 'medium')}{card(t['low'], 'low')}
</div>

<h2>Observability</h2>
<div class="cards">
{card(t['mapped'], 'mapped', 'ac')}{card(t['blind'], 'blind', 'crit')}
{card(t['unmapped'], 'unmapped', 'high')}
</div>
{notes}

{corro}

<h2>Repos</h2>
<div class="tw"><table>
<thead><tr><th>Repo</th><th>Tier</th><th>Kind</th><th>State</th><th>Reviewed</th>
<th>Dynatrace</th><th>C</th><th>H</th><th>M</th><th>L</th><th>Gaps</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>

</div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", default="config/repos.json")
    ap.add_argument("--out", default=".", help="workspace directory to write into")
    a = ap.parse_args()

    profile, repos, corr = load(Path(a.repos))
    t = totals(repos)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    (out / "review-status.md").write_text(md(profile, repos, corr, t), encoding="utf-8")
    (out / "review-status.html").write_text(html(profile, repos, corr, t), encoding="utf-8")

    print(f"  {t['repos']} repos: {t['reviewed']} reviewed, {t['partial']} partial, {t['queued']} queued")
    print(f"  findings: {t['critical']}C {t['high']}H {t['medium']}M {t['low']}L "
          f"| {t['gaps']} evidence gaps")
    print(f"  observability: {t['mapped']} mapped, {t['blind']} blind, {t['unmapped']} unmapped")
    print(f"  -> {out / 'review-status.md'}")
    print(f"  -> {out / 'review-status.html'}")


if __name__ == "__main__":
    main()
