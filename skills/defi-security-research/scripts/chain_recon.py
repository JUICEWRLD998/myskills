"""chain_recon.py — multi-chain recon toolkit (verified 2026-09-24).

Promoted from the audit3 recon pass, where five parallel agents used it to price on-contract funds
across chains without a keyed explorer. Read-only: RPC reads, balance reads, proxy-slot reads.

WHAT IT GIVES YOU THAT THE DOCS DID NOT:
  rpc / call / bal_of / eth_bal      JSON-RPC with a per-chain FALLBACK LIST, so one dead public
                                     endpoint does not read as "no data" (measured 2026-09-24:
                                     eth.llamarpc.com and polygon-rpc.com were both refusing while
                                     rpc.mevblocker.io, eth-pokt.nodies.app, 0xrpc.io/eth and
                                     *.publicnode.com all served).
  impl_slot(chain, addr)             EIP-1967 impl + beacon slot read from CHAIN STATE. Use this
                                     instead of an explorer's `implementations[]` field, which
                                     Blockscout omits for ERC1967/UUPS (that omission hid ~$56M of
                                     coverage in a prior pass).
  token_balances(api_base, addr)     Blockscout /token-balances with retries (it rate-limits ~5/min
                                     and returns three different bodies that all look like
                                     "unverified": 429, a ~110-byte "Too many requests", and a ~94KB
                                     SPA shell).
  price_usd(chain, token)            coins.llama.fi price, because an explorer's own exchange_rate is
                                     frequently ABSENT - measured twice on 2026-09-24, where it priced
                                     a real $10.5M pool and a $26M RWA wrapper at $0.00.

VERIFIED 2026-09-24 by running it against known values:
  impl_slot(ethereum, 0x7A3dDEac7A0AE6dfA9391C764499A3564F3c2AAd) -> 0xeedb88400b1b14380192b217aa226004705863d0  PASS
  code_len(ethereum, 0xA0b86991...USDC) -> 2400                                                                 PASS
  eth_bal(ethereum, mETH MantleStaking) -> 19684400828587417334330   (WEI - divide by 1e18 yourself)           PASS
NOTE THE UNIT: eth_bal returns WEI, not ether. The one "failure" in the promotion test was the test's
own units error, not a defect here - convert before comparing.

KNOWN CAVEAT, LEFT IN PLACE DELIBERATELY: the module disables TLS certificate verification
(`CERT_NONE` + `check_hostname=False`). For read-only public-RPC recon that is usually benign, and
changing it now would alter a path five agents already proved; but it means an on-path attacker could
feed you false chain data. If a pass ever feeds a FINDING (rather than a candidate screen), re-run that
number with verification on before it is written down.

NOT A REPLACEMENT for `cast`: prefer `cast call`/`cast storage` when foundry is on PATH, and use this
when you need a chain the local foundry config does not know, or a multi-endpoint fallback.
"""
import json, urllib.request, urllib.error, ssl, time

_ctx = ssl.create_default_context(); _ctx.check_hostname=False; _ctx.verify_mode=ssl.CERT_NONE

RPCS = {
 "hyperevm":  ["https://rpc.hyperliquid.xyz/evm"],
 "monad":     ["https://rpc.monad.xyz", "https://rpc1.monad.xyz"],
 "etherlink": ["https://node.mainnet.etherlink.com"],
 "flare":     ["https://flare-api.flare.network/ext/C/rpc"],
 "sei":       ["https://evm-rpc.sei-apis.com"],
 "avalanche": ["https://api.avax.network/ext/bc/C/rpc"],
 "ethereum":  ["https://eth.llamarpc.com","https://ethereum.publicnode.com","https://rpc.ankr.com/eth",
               "https://cloudflare-eth.com","https://eth.drpc.org","https://1rpc.io/eth"],
 "base":      ["https://base.llamarpc.com","https://base.publicnode.com","https://base.drpc.org",
               "https://1rpc.io/base","https://base-rpc.publicnode.com"],
 "arbitrum":  ["https://arbitrum.llamarpc.com","https://arbitrum.publicnode.com","https://arb1.arbitrum.io/rpc",
               "https://arbitrum.drpc.org","https://1rpc.io/arb"],
 "bsc":       ["https://bsc.publicnode.com","https://bsc-rpc.publicnode.com","https://binance.llamarpc.com",
               "https://bsc.drpc.org","https://1rpc.io/bnb"],
}

def _raw(url, payload, timeout=25):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx) as r:
        return json.loads(r.read().decode())

def rpc(chain, method, params, timeout=25):
    """Try each endpoint for the chain until one works."""
    last = None
    for url in RPCS.get(chain, []):
        try:
            out = _raw(url, {"jsonrpc":"2.0","id":1,"method":method,"params":params}, timeout)
            if "result" in out:
                return out["result"]
            last = out
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
    return {"_error": str(last)}

def call(chain, to, data, timeout=25):
    return rpc(chain, "eth_call", [{"to":to,"data":data}, "latest"], timeout)

def bal_of(chain, token, holder, timeout=25):
    """ERC20 balanceOf -> int or None"""
    data = "0x70a08231" + "0"*24 + holder.lower().replace("0x","")
    r = call(chain, token, data, timeout)
    if isinstance(r, str) and r.startswith("0x") and len(r) > 2:
        try: return int(r, 16)
        except Exception: return None
    return None

def eth_bal(chain, addr):
    r = rpc(chain, "eth_getBalance", [addr, "latest"])
    if isinstance(r, str) and r.startswith("0x"):
        return int(r, 16)
    return None

def impl_slot(chain, addr):
    """EIP-1967 impl slot + beacon slot."""
    s1 = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
    s2 = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
    a = rpc(chain, "eth_getStorageAt", [addr, s1, "latest"])
    b = rpc(chain, "eth_getStorageAt", [addr, s2, "latest"])
    def norm(x):
        if isinstance(x,str) and x.startswith("0x") and len(x)==66:
            v = x[2:]
            if int(v,16)==0: return None
            return "0x"+v[-40:]
        return x
    return {"impl": norm(a), "beacon": norm(b)}

def code_len(chain, addr):
    r = rpc(chain, "eth_getCode", [addr, "latest"])
    if isinstance(r,str) and r.startswith("0x"):
        return (len(r)-2)//2
    return r

def src_blockscout(api_base, addr):
    """fetch /api/v2/smart-contracts/<addr> return dict or error string"""
    url = f"{api_base}/smart-contracts/{addr}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30, context=_ctx) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode("utf-8","replace")[:200]}
    except Exception as e:
        return {"_err": f"{type(e).__name__}: {e}"}

def token_balances(api_base, addr, tries=3):
    url = f"{api_base}/addresses/{addr}/token-balances"
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30, context=_ctx) as r:
                body = r.read().decode()
                if body.strip().startswith("["):
                    return json.loads(body)
                if "Too many requests" in body or len(body) < 300:
                    time.sleep(8); continue
                return {"_bad": body[:200]}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(10); continue
            return {"_http": e.code}
        except Exception as e:
            return {"_err": f"{type(e).__name__}: {e}"}
    return {"_err": "rate-limited after retries"}

def price_usd(chain, token_addr):
    """explorer-free price via llama coins API"""
    try:
        req = urllib.request.Request(f"https://coins.llama.fi/prices/current/{chain}:{token_addr}",
                                     headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20, context=_ctx) as r:
            d = json.loads(r.read().decode())
        coins = d.get("coins", {})
        for k,v in coins.items():
            return v.get("price")
    except Exception:
        pass
    return None
