#!/usr/bin/env python
"""sourcify_pull_sources.py - pull a verified contract's sources WITH their original paths, plus the
compilation settings, and scaffold a Foundry project that should reproduce the deployed bytecode.

Why this exists: the naive dump that flattens files to basenames collides and LOSES sources (PRBMath
ships both sd59x18/Math.sol and ud60x18/Math.sol; the second one holds exp/ln). Losing a dependency
silently invalidates any compile-parity conclusion.

Usage:
    python sourcify_pull_sources.py <chainId> <address> <outdir> [--sourcify URL]
Example:
    python sourcify_pull_sources.py 1 0x0000f07d2B5F1Ddf3244b8780F972f306EFd2888 ./deployed_sources

Writes:
    <outdir>/<ContractName>/<original path...>.sol     full source tree
    <outdir>/<ContractName>/_sourcify.json             raw payload (match verdict, metadata)
    <outdir>/<ContractName>/_foundry.toml              settings copied from compilerSettings
    <outdir>/<ContractName>/_PATHS.txt                 declared source paths (audit trail)
"""
import json
import os
import subprocess
import sys

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def curl(url, timeout=60):
    """Sourcify is friendly, but keep curl for consistency with the explorer fetchers."""
    r = subprocess.run(["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True)
    return r.stdout or ""


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 1
    chain_id, address, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    base = "https://sourcify.dev/server/v2/contract"
    url = f"{base}/{chain_id}/{address}?fields=sources,metadata,compilation"
    raw = curl(url)
    if not raw.strip().startswith("{"):
        print(f"Sourcify returned non-JSON (job may still be running); got: {raw[:200]}")
        return 2
    j = json.loads(raw)

    comp = (j.get("compilation") or {})
    sources = comp.get("sources") or {}
    settings = (comp.get("compilerSettings") or {})
    if not sources:
        print("no sources in payload — contract may be only partially verified")
        print("match:", j.get("match"))
        return 3

    # contract name from the metadata compilation target when available
    target = "contract"
    try:
        tgt = (j.get("metadata") or {}).get("settings", {}).get("compilationTarget") or {}
        if tgt:
            target = list(tgt.keys())[0].split("/")[-1].replace(".sol", "") or target
    except Exception:
        pass
    contract_dir = os.path.join(outdir, target)

    written, skipped = 0, []
    for path, body in sources.items():
        content = body.get("content") if isinstance(body, dict) else body
        if content is None:
            # keccak-only entries cannot be reconstructed locally
            skipped.append(path)
            continue
        dest = os.path.join(contract_dir, path.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        written += 1

    os.makedirs(contract_dir, exist_ok=True)
    with open(os.path.join(contract_dir, "_sourcify.json"), "w", encoding="utf-8") as fh:
        json.dump(j, fh, indent=1)
    with open(os.path.join(contract_dir, "_PATHS.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(sources)) + "\n")

    opt = settings.get("optimizer") or {}
    evm = settings.get("evmVersion") or "cancun"
    via_ir = bool((settings.get("viaIR") if "viaIR" in settings else None))
    meta = settings.get("metadata") or {}
    remaps = j.get("compilerSettings", {}).get("remappings") or settings.get("remappings") or []
    toml = [
        "[profile.default]",
        'src = "src"',
        'out = "out"',
        'libs = ["lib"]',
        f'solc_version = "{(comp.get("compilerVersion") or "").split("+")[0] or "0.8.26"}"',
        f'evm_version = "{evm}"',
        f'via_ir = {str(via_ir).lower()}',
        f'optimizer = {str(bool(opt.get("enabled"))).lower()}',
        f'optimizer_runs = {opt.get("runs", 200)}',
        f'bytecode_hash = "{meta.get("bytecodeHash", "ipfs")}"',
        f'cbor_metadata = {str(bool(meta.get("appendCBOR", True))).lower()}',
        "remappings = [",
    ]
    for rm in remaps:
        toml.append(f'    "{rm}",')
    toml.append("]")
    with open(os.path.join(contract_dir, "_foundry.toml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(toml) + "\n")

    print(f"match: {j.get('match')}")
    print(f"compiler: {comp.get('compilerVersion')}  viaIR={via_ir}  runs={opt.get('runs')}  evm={evm}")
    print(f"wrote {written} source files -> {contract_dir}")
    if skipped:
        print(f"SKIPPED {len(skipped)} keccak-only entries (no content): {skipped[:5]}")
    print("next: copy the tree into a forge project, build with _foundry.toml, then run")
    print("      scripts/parity_check_immutables.py <artifact.json> <address> <rpc>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
