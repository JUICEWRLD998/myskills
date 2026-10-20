#!/usr/bin/env python
"""Verify a GitHub repo actually offers a private vulnerability-reporting door BEFORE telling the user to
submit there. Validated 2026-09-12 (Sato: SATO-Community/sato-docs).

Usage:
    python check_github_intake_channel.py SATO-Community/sato-docs

Checks, all read-only and unauthenticated:
  1. account type + public repo list (TRAP: for a *User* account, /orgs/<account>/repos returns an EMPTY body
     that reads exactly like "no repositories" -- must fall back to /users/<account>/repos)
  2. whether the repo's Security tab exposes "Report a vulnerability" (= Private Vulnerability Reporting on)
  3. SECURITY.md, fetched with a raw -> jsDelivr fallback (raw.githubusercontent 503s intermittently), printing
     the lines that decide scope (component/address tables, the intake wording)

Exit code 0 = PVR looks enabled, 1 = not (then use the fallback ladder in the skill reference), 2 = usage/network.
"""

import json
import subprocess
import sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def curl(url, extra=None):
    cmd = ["curl", "-sL", "-m", "25", "-A", UA]
    if extra:
        cmd += extra
    cmd.append(url)
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=40).stdout
    except Exception as exc:  # pragma: no cover - network/tooling dependent
        return "ERR:%s" % exc


def api(path):
    raw = curl("https://api.github.com" + path, ["-H", "Accept: application/vnd.github+json"])
    try:
        return json.loads(raw)
    except Exception:
        return None


def main():
    if len(sys.argv) != 2 or "/" not in sys.argv[1]:
        print(__doc__)
        return 2
    owner, repo = sys.argv[1].split("/", 1)

    acct = api("/users/" + owner) or {}
    print("account      : %s  (type=%s, public_repos=%s)" % (owner, acct.get("type"), acct.get("public_repos")))

    repos = api("/users/%s/repos?per_page=30" % owner)
    if isinstance(repos, list):
        names = [r.get("full_name") for r in repos]
        print("repos        : %s" % ", ".join(n for n in names if n))
        for r in repos:
            if r.get("full_name") == "%s/%s" % (owner, repo):
                print("target repo  : issues=%s pushed_at=%s archived=%s" % (r.get("has_issues"), r.get("pushed_at"), r.get("archived")))
    else:
        print("repos        : <unavailable> (rate limit? try again in a minute)")

    sec = curl("https://github.com/%s/%s/security" % (owner, repo))
    pvr = "report a vulnerability" if "report a vulnerability" in sec.lower() else None
    print("PVR button   : %s" % ("PRESENT -> private advisory can be opened (login required to submit)" if pvr else "not found"))
    if not pvr:
        print("               -> do NOT post details publicly; use the minimal-public-issue fallback ladder")

    md = curl("https://raw.githubusercontent.com/%s/%s/HEAD/SECURITY.md" % (owner, repo))
    if md.startswith("ERR") or len(md) < 50:
        md = curl("https://cdn.jsdelivr.net/gh/%s/%s@HEAD/SECURITY.md" % (owner, repo))
    interesting = [
        l.strip() for l in md.splitlines()
        if any(k in l.lower() for k in ("0x", "scope", "disclos", "advisories", "report", "component"))
    ]
    print("SECURITY.md  : %d lines fetched; lines that decide scope/intake:" % len(md.splitlines()))
    for line in interesting[:14]:
        print("   | " + line[:160])
    print()
    print("Next: confirm the SCOPE table names the deployed contract addresses (not just the docs repo), then")
    print("paste the paste-ready submission into: https://github.com/%s/%s/security/advisories/new" % (owner, repo))
    return 0 if pvr else 1


if __name__ == "__main__":
    sys.exit(main())
