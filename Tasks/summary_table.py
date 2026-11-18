"""A3: daily summary table per station - Python loops vs SQL GROUP BY."""
import random, sqlite3, time, tracemalloc

def make(n):
    rnd = random.Random(3)
    return [(f"S{rnd.randrange(12):02d}", f"2026-10-{rnd.randrange(1, 32):02d}",
             None if rnd.random() < 0.05 else round(rnd.uniform(5, 200), 1)) for _ in range(n)]

def python_summary(rows):
    acc = {}
    for st, day, pm in rows:
        if pm is None: continue
        a = acc.setdefault((st, day), [pm, pm, 0.0, 0])      # min, max, sum, count
        a[0] = min(a[0], pm); a[1] = max(a[1], pm); a[2] += pm; a[3] += 1
    return {k: (a[0], a[1], round(a[2] / a[3], 2), a[3]) for k, a in sorted(acc.items())}

SQL = """SELECT station, day, MIN(pm25), MAX(pm25), ROUND(AVG(pm25),2), COUNT(pm25)
         FROM aq GROUP BY station, day ORDER BY station, day"""

def sql_summary(con):
    return {(r[0], r[1]): r[2:] for r in con.execute(SQL)}

rows = make(2000)
con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
con.executemany("INSERT INTO aq VALUES (?,?,?)", rows)
py, sq = python_summary(rows), sql_summary(con)
print("daily_summary(station, day, min, max, mean, n_valid) - first rows:")
for k in list(py)[:4]: print("  ", k, py[k])
print("Python loops and GROUP BY agree:", py.keys() == sq.keys() and all(abs(a - b) < 0.011 for k in py for a, b in zip(py[k], sq[k])))

print("\nn readings | Python time  peak mem | SQL time (data already in DB)")
for n in (10_000, 100_000, 1_000_000):
    rows = make(n)
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
    con.executemany("INSERT INTO aq VALUES (?,?,?)", rows)
    tracemalloc.start(); t0 = time.perf_counter(); python_summary(rows)
    tp = time.perf_counter() - t0; peak = tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
    t0 = time.perf_counter(); sql_summary(con); ts = time.perf_counter() - t0
    print(f"{n:>10,} | {tp:8.3f}s {peak / 1e3:7.0f} KB | {ts:8.3f}s")
