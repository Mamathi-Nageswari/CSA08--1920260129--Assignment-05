"""B3: daily mean PM2.5 per station - csv loops vs pandas groupby vs SQL GROUP BY."""
import cProfile, csv, io, os, pstats, sqlite3, statistics, time, tracemalloc
import pandas as pd
from gen_data import write_csv

def num(x):
    try: v = float(x)
    except ValueError: return None
    return v if 0 <= v <= 999 else None

def plain(path):
    groups = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = num(r["pm25"])
            if v is not None: groups.setdefault((r["station"], r["date"]), []).append(v)
    return {k: round(statistics.mean(v), 2) for k, v in groups.items()}

def running(path):                                        # alternative: running sum and count
    acc = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = num(r["pm25"])
            if v is not None:
                a = acc.setdefault((r["station"], r["date"]), [0.0, 0]); a[0] += v; a[1] += 1
    return {k: round(s / c, 2) for k, (s, c) in acc.items()}

def with_pandas(path):
    df = pd.read_csv(path, na_values=["NA"])
    df = df[(df.pm25 >= 0) & (df.pm25 <= 999)]
    return df.groupby(["station", "date"]).pm25.mean().round(2).to_dict()

def load_db(path):
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE r (station TEXT, day TEXT, pm25 REAL)")
    with open(path, encoding="utf-8") as f:
        con.executemany("INSERT INTO r VALUES (?,?,?)", ((r["station"], r["date"], num(r["pm25"])) for r in csv.DictReader(f)))
    return con
def with_sql(con):
    return {(s, d): m for s, d, m in con.execute("SELECT station, day, ROUND(AVG(pm25),2) FROM r WHERE pm25 IS NOT NULL GROUP BY station, day")}

def same(a, b): return a.keys() == b.keys() and all(abs(a[k] - b[k]) < 0.011 for k in a)

if __name__ == "__main__":
    write_csv("small.csv", 3, days=3)
    a, b, c = plain("small.csv"), with_pandas("small.csv"), with_sql(load_db("small.csv"))
    print("B3.1 small data (3 stations x 3 days):")
    for k in list(a)[:4]: print(f"   {k}: loops {a[k]}  pandas {b[k]}  SQL {c[k]}")
    print("   all three agree:", same(a, b) and same(a, c), f"({len(a)} station-days)")

    print("\nB3.2 one year of hourly data")
    print(f"{'stations':>8} {'rows':>10} | {'loops':>7} {'pandas':>7} {'SQL load':>9} {'SQL query':>9}")
    for n in (1, 12, 120):
        p = f"year_{n}.csv"
        if not os.path.exists(p): write_csv(p, n)
        t = []
        for f in (plain, with_pandas):
            t0 = time.perf_counter(); f(p); t.append(time.perf_counter() - t0)
        t0 = time.perf_counter(); con = load_db(p); t.append(time.perf_counter() - t0)
        t0 = time.perf_counter(); with_sql(con); t.append(time.perf_counter() - t0)
        print(f"{n:>8} {n * 8760:>10,} | {t[0]:6.2f}s {t[1]:6.2f}s {t[2]:8.2f}s {t[3]:8.3f}s")

    print("\nB3.3 cProfile of the plain-Python version (12 stations), top 6 by total time")
    pr = cProfile.Profile(); pr.enable(); plain("year_12.csv"); pr.disable()
    s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(6)
    lines = s.getvalue().splitlines(); i = next(i for i, l in enumerate(lines) if "ncalls" in l)
    print("\n".join(l.replace("/usr/lib/python3.10/", "").replace(os.getcwd() + "/", "") for l in lines[i:i + 7]))

    print("\nAlternative: store all readings + statistics.mean vs running sum (120 stations)")
    for f in (plain, running):
        tracemalloc.start(); t0 = time.perf_counter(); r = f("year_120.csv")
        print(f"   {f.__name__:<8} {time.perf_counter() - t0:6.2f}s  peak {tracemalloc.get_traced_memory()[1] / 1e6:6.1f} MB")
        tracemalloc.stop()
