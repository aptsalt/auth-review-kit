#!/usr/bin/env python3
"""
dt_pull.py — pull Dynatrace problems/telemetry through an ALREADY-AUTHENTICATED browser session.

Why this shape: Dynatrace in an enterprise sits behind SSO/MFA. Rather than handling credentials or
minting an API token, this attaches to a Chrome/Edge you logged into yourself over the DevTools
protocol, and reuses that session. Nothing secret is ever stored by this script.

Two modes:

  api      Same-origin fetch() from inside the authenticated page against Dynatrace REST endpoints.
           Fast and repeatable. Endpoint shapes differ by tenant version, so the first successful
           path is remembered in config/dynatrace.local.json.

  capture  Passive. You browse to Problems (set the window to 30d) and the script records the JSON
           responses the UI itself fetches. Slower, but works on any tenant version without knowing
           a single endpoint. Use this first; switch to `api` once a path is known.

Setup (once):
  1. Close Chrome/Edge completely.
  2. Start it with remote debugging:
       Chrome: chrome.exe --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\\dt-profile"
       Edge:   msedge.exe --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\\dt-profile"
     (or run this script with --launch, which does it for you)
  3. Log into Dynatrace in that window, normally, through SSO.

Then:
  python dt_pull.py --mode capture --minutes 3
  python dt_pull.py --mode api --window 30d

Output:
  _dynatrace/raw/<timestamp>-<n>.json     every captured payload, untouched
  _dynatrace/problems.json                normalised problem list
  _dynatrace/pull-manifest.json           what ran, when, what worked, what did not
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright is required:  pip install playwright  &&  playwright install chromium")

OUT = Path("_dynatrace")
RAW = OUT / "raw"
CFG = Path("config/dynatrace.local.json")

# URL fragments that indicate a payload worth keeping in capture mode.
CAPTURE_HINTS = (
    "problem", "/api/v2/", "/rest/", "entity", "metrics", "events",
    "query:execute", "davis", "slo", "alerting",
)

# Candidate endpoints, tried in order. Tenants differ; the first that returns JSON wins.
API_CANDIDATES = [
    "/api/v2/problems?from=now-{w}&pageSize=500",
    "/api/v2/problems?from=now-{w}",
    "/rest/problems?relativeTime={w}",
    "/rest/dispatcher/problems/list?relativeTime={w}",
]


def log(msg):
    print(f"  {msg}", flush=True)


def load_cfg():
    if CFG.exists():
        try:
            return json.loads(CFG.read_text(encoding="utf-8"))
        except Exception:
            log(f"! {CFG} is not valid JSON — ignoring it")
    return {}


def save_cfg(cfg):
    CFG.parent.mkdir(parents=True, exist_ok=True)
    CFG.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def launch_browser(port):
    """Start Chrome or Edge with remote debugging on an isolated profile."""
    local = os.environ.get("LOCALAPPDATA", str(Path.home()))
    profile = str(Path(local) / "dt-profile")
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    exe = next((c for c in candidates if Path(c).exists()), None)
    if not exe:
        sys.exit("Could not find Chrome or Edge. Start one manually with --remote-debugging-port.")
    subprocess.Popen([exe, f"--remote-debugging-port={port}", f"--user-data-dir={profile}"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log(f"launched {Path(exe).name} on port {port} (profile: {profile})")
    log("log into Dynatrace in that window, then re-run without --launch")


def find_dt_page(browser, tenant_hint):
    """Find an open tab that looks like Dynatrace."""
    pages = [p for ctx in browser.contexts for p in ctx.pages]
    if not pages:
        return None
    needle = (tenant_hint or "dynatrace").lower()
    for p in pages:
        try:
            if needle in (p.url or "").lower():
                return p
        except Exception:
            continue
    for p in pages:
        try:
            if "dynatrace" in (p.url or "").lower():
                return p
        except Exception:
            continue
    return None


def normalise(payloads):
    """Best-effort flattening of whatever Dynatrace returned into a common problem shape.

    Tenant versions disagree on field names, so this keeps the untouched payload on every record.
    A field we could not find is None — never a guess. Correlation treats None as unknown, not absent.
    """
    problems, seen = [], set()

    def dig(obj):
        """Yield dict nodes that look like a problem."""
        if isinstance(obj, dict):
            keys = set(obj.keys())
            if ({"problemId"} & keys) or ({"displayId"} & keys) or \
               ({"title", "status"} <= keys) or ({"problemFilters", "startTime"} <= keys):
                yield obj
            for v in obj.values():
                yield from dig(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from dig(v)

    def first(d, *names):
        for n in names:
            if isinstance(d, dict) and d.get(n) not in (None, "", []):
                return d[n]
        return None

    def entities(d):
        out = []
        for key in ("affectedEntities", "impactedEntities", "entityTags", "rootCauseEntity", "entities"):
            v = d.get(key)
            if isinstance(v, list):
                for e in v:
                    if isinstance(e, dict):
                        n = first(e, "name", "displayName", "entityName")
                        if n:
                            out.append(n)
                    elif isinstance(e, str):
                        out.append(e)
            elif isinstance(v, dict):
                n = first(v, "name", "displayName", "entityName")
                if n:
                    out.append(n)
        return sorted(set(out))

    for p in payloads:
        for d in dig(p):
            pid = first(d, "problemId", "displayId", "id")
            title = first(d, "title", "displayName", "problemTitle")
            if not pid and not title:
                continue
            k = f"{pid}|{title}"
            if k in seen:
                continue
            seen.add(k)
            problems.append({
                "id": pid,
                "title": title,
                "status": first(d, "status", "problemStatus"),
                "severity": first(d, "severityLevel", "severity", "impactLevel"),
                "impact": first(d, "impactLevel", "impact"),
                "start": first(d, "startTime", "start", "from"),
                "end": first(d, "endTime", "end", "to"),
                "entities": entities(d),
                "management_zones": [
                    z.get("name") for z in (d.get("managementZones") or [])
                    if isinstance(z, dict) and z.get("name")
                ],
                "affected_count": first(d, "affectedCount", "impactedCount"),
                "_raw": d,
            })
    return problems


def run_api(page, origin, window, cfg):
    """Fetch from inside the page so the browser attaches session cookies and headers itself."""
    payloads, worked, failed = [], None, []
    known = cfg.get("problems_endpoint")
    order = ([known] if known else []) + [c for c in API_CANDIDATES if c != known]

    for tmpl in order:
        path = tmpl.format(w=window)
        url = origin.rstrip("/") + path
        try:
            res = page.evaluate(
                """async (u) => {
                    try {
                        const r = await fetch(u, {credentials:'include', headers:{'Accept':'application/json'}});
                        const t = await r.text();
                        return {ok: r.ok, status: r.status, body: t.slice(0, 4000000)};
                    } catch (e) { return {ok:false, status:0, body:String(e)}; }
                }""", url)
        except Exception as e:
            failed.append({"path": path, "error": str(e)})
            continue

        if not res.get("ok"):
            failed.append({"path": path, "status": res.get("status")})
            log(f"  {res.get('status')}  {path}")
            continue
        try:
            data = json.loads(res["body"])
        except Exception:
            failed.append({"path": path, "status": res.get("status"), "error": "not JSON"})
            log(f"  200 but not JSON  {path}")
            continue

        payloads.append(data)
        worked = tmpl
        log(f"  ok  {path}")
        break

    if worked:
        cfg["problems_endpoint"] = worked
        save_cfg(cfg)
    return payloads, worked, failed


def run_capture(page, minutes):
    """Record JSON responses the Dynatrace UI fetches while you browse."""
    payloads = []

    def on_response(res):
        try:
            url = res.url
            if not any(h in url.lower() for h in CAPTURE_HINTS):
                return
            ctype = (res.headers or {}).get("content-type", "")
            if "json" not in ctype.lower():
                return
            data = res.json()
        except Exception:
            return
        payloads.append({"_url": url, "_data": data})
        log(f"  captured  {url[:110]}")

    page.on("response", on_response)

    print()
    log("CAPTURE MODE — in the browser window:")
    log("  1. open Problems")
    log("  2. set the time window to the last 30 days")
    log("  3. scroll the list so the UI actually loads the pages")
    log(f"  recording for {minutes} minute(s) — Ctrl+C to stop early")
    print()

    deadline = time.time() + minutes * 60
    try:
        while time.time() < deadline:
            page.wait_for_timeout(1000)
    except KeyboardInterrupt:
        log("stopped early")

    page.remove_listener("response", on_response)
    return [p["_data"] for p in payloads], [p["_url"] for p in payloads]


def main():
    ap = argparse.ArgumentParser(description="Pull Dynatrace data via an authenticated browser session.")
    ap.add_argument("--mode", choices=["api", "capture"], default="capture")
    ap.add_argument("--port", type=int, default=9222, help="CDP port of the logged-in browser")
    ap.add_argument("--window", default="30d", help="relative window for api mode (e.g. 30d, 7d)")
    ap.add_argument("--minutes", type=int, default=3, help="capture duration")
    ap.add_argument("--tenant", default=None, help="substring identifying the tenant tab/origin")
    ap.add_argument("--launch", action="store_true", help="start a debuggable browser and exit")
    args = ap.parse_args()

    cfg = load_cfg()
    tenant_hint = args.tenant or cfg.get("tenant_hint")

    if args.launch:
        launch_browser(args.port)
        return

    RAW.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.connect_over_cdp(f"http://localhost:{args.port}")
        except Exception as e:
            sys.exit(
                f"Could not attach to a browser on port {args.port}.\n"
                f"  {e}\n\n"
                f"Start one with:  python {Path(__file__).name} --launch\n"
                f"then log into Dynatrace in that window and re-run."
            )

        page = find_dt_page(browser, tenant_hint)
        if not page:
            sys.exit(
                "Attached, but no Dynatrace tab was found.\n"
                "Open your Dynatrace tenant in that browser window and re-run.\n"
                "If the URL does not contain 'dynatrace', pass --tenant <substring>."
            )

        m = re.match(r"^https?://[^/]+", page.url or "")
        if not m:
            sys.exit(f"The Dynatrace tab has no usable URL ({page.url!r}). Navigate to your tenant and re-run.")
        origin = m.group(0)
        log(f"attached to {origin}")
        cfg["tenant_hint"] = tenant_hint or origin.split("//")[-1].split(".")[0]

        if args.mode == "api":
            payloads, worked, failed = run_api(page, origin, args.window, cfg)
            urls = [worked] if worked else []
            if not payloads:
                log("! no endpoint returned JSON — run again with --mode capture")
        else:
            payloads, urls = run_capture(page, args.minutes)
            failed = []

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for i, p in enumerate(payloads):
        (RAW / f"{stamp}-{i:03d}.json").write_text(
            json.dumps(p, indent=2, ensure_ascii=False), encoding="utf-8")

    problems = normalise(payloads)
    (OUT / "problems.json").write_text(
        json.dumps(problems, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "window": args.window if args.mode == "api" else "whatever the UI was showing",
        "origin": origin,
        "payloads": len(payloads),
        "problems_normalised": len(problems),
        "sources": urls,
        "failed_endpoints": failed,
        "caveat": (
            "This is what this pull saw. Absence of a problem here is not evidence of absence in "
            "production — check the window, the management zone filter, and whether the service is "
            "instrumented at all before reading silence as a clean result."
        ),
    }
    (OUT / "pull-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    save_cfg(cfg)

    print()
    log(f"payloads saved : {len(payloads)}  ->  {RAW}")
    log(f"problems       : {len(problems)}  ->  {OUT / 'problems.json'}")
    log(f"manifest       : {OUT / 'pull-manifest.json'}")
    if problems:
        ents = sorted({e for p in problems for e in p["entities"]})
        log(f"distinct entities seen: {len(ents)}")
        for e in ents[:15]:
            log(f"    {e}")
        if len(ents) > 15:
            log(f"    ... and {len(ents) - 15} more")


if __name__ == "__main__":
    main()
