#!/usr/bin/env python
"""fetch_explorer.py <url> [--out file] [--json a.b] -- fetch a Cloudflare-walled explorer URL.

Cloudflare on Blockscout instances returns "Just a moment..." to sparse clients but passes a FULL
browser header set. IMPORTANT: this must shell out to curl -- python urllib/requests get 403 even
with byte-identical headers, because Cloudflare fingerprints the TLS/JA3 stack. Validated on
robinhoodchain.blockscout.com 2026-09-10.
"""
import json, subprocess, sys, urllib.parse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
CHALLENGE = ("Just a moment", "cf-browser-verification", "challenges.cloudflare.com")
CURL_HEADERS = [
    "-A", UA,
    "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "-H", "Accept-Language: en-US,en;q=0.9",
    "-H", 'sec-ch-ua: "Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "-H", "sec-ch-ua-mobile: ?0",
    "-H", 'sec-ch-ua-platform: "Windows"',
    "-H", "Sec-Fetch-Dest: document",
    "-H", "Sec-Fetch-Mode: navigate",
    "-H", "Sec-Fetch-Site: none",
    "-H", "Upgrade-Insecure-Requests: 1",
    "--compressed",
]


def get(url, timeout=45):
    cmd = ["curl", "-s", "--max-time", str(timeout)] + CURL_HEADERS + [url]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15).stdout or ""
    except Exception as e:
        return f"__FAIL__{e}"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    target = sys.argv[1]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    q = urllib.parse.quote(target, safe="")
    routes = [target,
              f"https://api.allorigins.win/raw?url={q}",
              f"https://api.codetabs.com/v1/proxy?quest={urllib.parse.quote(target, safe=':/?&=')}"]
    body = None
    for url in routes:
        b = get(url)
        if not b or any(c in b[:2000] for c in CHALLENGE):
            print(f"[fail] {url.split('/')[2]}", file=sys.stderr)
            continue
        body = b
        print(f"[ok] via {url.split('/')[2]} ({len(b)} bytes)", file=sys.stderr)
        break
    if body is None:
        print("ALL ROUTES FAILED", file=sys.stderr)
        return 1
    if out:
        open(out, "w", encoding="utf-8").write(body)
        print(f"saved -> {out}", file=sys.stderr)
    try:
        j = json.loads(body)
        if "--json" in sys.argv:
            for k in sys.argv[sys.argv.index("--json") + 1].split("."):
                j = j[int(k)] if isinstance(j, list) else j[k]
        print(json.dumps(j, indent=1)[:20000])
    except Exception:
        print(body[:20000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
