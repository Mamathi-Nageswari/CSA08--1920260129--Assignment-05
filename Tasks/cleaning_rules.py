"""A2: cleaning rules, normalisation and standard formats, with drop vs fill comparison."""
import random, statistics, time
from datetime import datetime

def to_float(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if 0 <= v <= 999 else None          # negative / impossible -> missing

def drop(vals):   return [v for v in vals if v is not None]
def ffill(vals):
    out, last = [], None
    for v in vals:
        last = v if v is not None else last
        if last is not None: out.append(last)
    return out
def median_fill(vals):
    m = statistics.median(drop(vals))             # sorting: O(n log n)
    return [m if v is None else v for v in vals]

def dedupe(rows):
    seen, out = set(), []
    for r in rows:
        if r[:2] not in seen: seen.add(r[:2]); out.append(r)
    return out

def f_to_c(t): return round((t - 32) * 5 / 9, 1) if t > 60 else t   # a city reading > 60 must be Fahrenheit
def std_date(s):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try: return datetime.strptime(s.strip(), fmt).date().isoformat()
        except ValueError: pass
    raise ValueError(f"bad date {s!r}")
def std_name(s): return " ".join(s.split()).title()

def minmax(v):
    lo, hi = min(v), max(v); return [round((x - lo) / (hi - lo), 3) for x in v]
def zscore(v):
    m, s = statistics.mean(v), statistics.pstdev(v); return [round((x - m) / s, 2) for x in v]

raw = ["48", "", "NA", "-5", "60", "1500", "52", "", "300"]
vals = [to_float(x) for x in raw]
print("raw           :", raw)
print("parsed        :", vals)
for name, f in [("drop", drop), ("forward fill", ffill), ("median fill", median_fill)]:
    c = f(vals); print(f"{name:<14}: {c}  mean={statistics.mean(c):.1f}")
print("dedupe        :", dedupe([("Adyar", "2026-10-01 04", 40), ("Adyar", "2026-10-01 04", 40), ("Adyar", "2026-10-01 05", 42)]))
print("F->C          :", [f_to_c(t) for t in (84.2, 29.1, 99.5)])
print("dates         :", [std_date(d) for d in ("2026-10-01", "01/10/2026", "1-10-2026")])
print("names         :", [std_name(n) for n in (" adyar ", "ANNA  NAGAR", "guindy")])
clean = drop(vals)
print("min-max       :", minmax(clean))
print("z-score       :", zscore(clean), "(300 stands out at z > 1.5)")

print("\nAlternative: cost of each rule on n readings (5 % missing)")
for n in (10_000, 100_000, 1_000_000):
    v = [None if random.random() < 0.05 else random.uniform(0, 200) for _ in range(n)]
    ts = []
    for f in (drop, ffill, median_fill):
        t0 = time.perf_counter(); f(v); ts.append(time.perf_counter() - t0)
    print(f"n={n:>9,}: drop {ts[0]:.4f}s  ffill {ts[1]:.4f}s  median {ts[2]:.4f}s")
