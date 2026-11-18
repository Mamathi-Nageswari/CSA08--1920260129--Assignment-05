"""B1 alternative: csv module + loops vs pandas for cleaning and min-max normalisation."""
import csv, io, random, time, tracemalloc
import pandas as pd

def make(n):
    rnd = random.Random(1); buf = io.StringIO(); buf.write("station,date,pm25\n")
    for i in range(n):
        r = rnd.random()
        v = "" if r < .03 else "NA" if r < .05 else str(-3) if r < .06 else f"{rnd.uniform(5, 200):.1f}"
        buf.write(f"S{i % 12},2026-10-{i % 31 + 1:02d},{v}\n")
    return buf.getvalue()

def with_csv(text):
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        v = r["pm25"]
        if v in ("", "NA") or not 0 <= float(v) <= 999: continue
        rows.append((r["station"], r["date"], float(v)))
    vals = [p for *_, p in rows]; lo, hi = min(vals), max(vals)
    return [round((v - lo) / (hi - lo), 3) for v in vals]

def with_pandas(text):
    df = pd.read_csv(io.StringIO(text), na_values=["NA"]).dropna()
    df = df[(df.pm25 >= 0) & (df.pm25 <= 999)]
    return ((df.pm25 - df.pm25.min()) / (df.pm25.max() - df.pm25.min())).round(3)

print(f"{'rows':>10} | {'csv time':>9} {'peak MB':>8} | {'pandas time':>11} {'peak MB':>8} | same")
for n in (1_000, 100_000, 1_000_000):
    text = make(n); res = []
    for f in (with_csv, with_pandas):
        tracemalloc.start(); t0 = time.perf_counter(); out = f(text)
        res.append((time.perf_counter() - t0, tracemalloc.get_traced_memory()[1] / 1e6, list(out))); tracemalloc.stop()
    print(f"{n:>10,} | {res[0][0]:8.3f}s {res[0][1]:8.1f} | {res[1][0]:10.3f}s {res[1][1]:8.1f} | {res[0][2] == res[1][2]}")
