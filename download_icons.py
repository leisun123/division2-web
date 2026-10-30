#!/usr/bin/env python3
"""Download mapped game images from Agent537-coder/td2-optimizer into icons/gamedb/ (skips existing)."""
import os, sys, subprocess, concurrent.futures

HERE = os.path.dirname(os.path.abspath(__file__))
DL = os.path.join(HERE, "raw", "dl.txt")
BASE = "https://raw.githubusercontent.com/Agent537-coder/td2-optimizer/main/"

jobs = []
for line in open(DL):
    line = line.strip()
    if not line:
        continue
    rp, lp = line.split("\t")
    lp = os.path.join(HERE, lp)
    if not os.path.exists(lp):
        os.makedirs(os.path.dirname(lp), exist_ok=True)
        jobs.append((rp, lp))
print(f"need {len(jobs)} downloads")

def fetch(job):
    rp, lp = job
    r = subprocess.run(
        ["curl", "-s", "--max-time", "45", "-o", lp, BASE + rp],
        capture_output=True, text=True,
    )
    if r.returncode == 0 and os.path.getsize(lp) > 0:
        return None
    return (rp, r.stderr.strip()[:80])

ok = fail = 0
errs = []
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
    for res in ex.map(fetch, jobs):
        if res:
            fail += 1
            errs.append(res)
        else:
            ok += 1
print(f"done: {ok} ok, {fail} failed")
for rp, e in errs[:10]:
    print("  FAIL", rp, e)
sys.exit(1 if fail else 0)
