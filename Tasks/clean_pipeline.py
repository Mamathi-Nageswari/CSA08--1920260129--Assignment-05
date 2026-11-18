"""B1: cleaning pipeline (rules from A2), store in SQLite with executemany, SQL answers, charts."""
import csv, os, sqlite3, statistics, sys
from datetime import datetime
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from gen_data import write_csv

def std_name(s): return " ".join(s.split()).title()
def std_date(s):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try: return datetime.strptime(s.strip(), fmt).date().isoformat()
        except ValueError: pass
    return None
def num(x, hi=999):
    try: v = float(x)
    except ValueError: return None
    return v if 0 <= v <= hi else None
def to_c(t): return round((t - 32) * 5 / 9, 1) if t > 60 else t

def clean_rows(rows):
    out, seen = [], set()
    for r in rows:
        key = (std_name(r["station"]), std_date(r["date"]), int(r["hour"]))
        if key[1] is None or key in seen: continue         # bad date / duplicate
        seen.add(key)
        out.append(key + (num(r["pm25"]), num(r["pm10"]), to_c(float(r["temp"]))))
    return out

def ffill_pm(rows):                                        # missing PM2.5 -> previous value of same station
    last, out = {}, []
    for r in rows:
        pm = r[3] if r[3] is not None else last.get(r[0])
        if r[3] is not None: last[r[0]] = r[3]
        out.append(r[:3] + (pm,) + r[4:])
    return out

if __name__ == "__main__":
    with open("dirty.csv", encoding="utf-8") as f:
        raw = list(csv.DictReader(f))
    print("BEFORE"); [print("  ", list(r.values())) for r in raw]
    cleaned = ffill_pm(clean_rows(raw))
    print("AFTER  (station, day, hour, pm25, pm10, temp_c)"); [print("  ", r) for r in cleaned]

    if not os.path.exists("year_12.csv"): write_csv("year_12.csv", 12)
    with open("year_12.csv", encoding="utf-8") as f:
        rows = [(std_name(r["station"]), r["date"], int(r["hour"]), num(r["pm25"]), num(r["pm10"]), to_c(float(r["temp_f"])))
                for r in csv.DictReader(f)]
    rows = ffill_pm(rows)
    if os.path.exists("aq.db"): os.remove("aq.db")
    con = sqlite3.connect("aq.db")
    con.execute("CREATE TABLE readings (station TEXT, day TEXT, hour INTEGER, pm25 REAL, pm10 REAL, temp_c REAL, PRIMARY KEY (station, day, hour))")
    con.executemany("INSERT INTO readings VALUES (?,?,?,?,?,?)", rows); con.commit()
    print(f"\nB1.3 stored {con.execute('SELECT COUNT(*) FROM readings').fetchone()[0]} cleaned rows in aq.db")
    Q = {"avg PM2.5 of Adyar in October": "SELECT ROUND(AVG(pm25),2) FROM readings WHERE station='Adyar' AND day LIKE '2026-10%'",
         "worst station on 2026-11-05": "SELECT station, MAX(pm25) FROM readings WHERE day='2026-11-05'",
         "Guindy days with daily average > 60": "SELECT COUNT(*) FROM (SELECT day FROM readings WHERE station='Guindy' GROUP BY day HAVING AVG(pm25) > 60)"}
    for k, q in Q.items(): print(f"   {k:<38} {con.execute(q).fetchone()}")

    trend = con.execute("SELECT day, AVG(pm25) FROM readings WHERE station='Adyar' AND day LIKE '2026-10%' GROUP BY day").fetchall()
    plt.figure(figsize=(8, 3.6)); plt.plot([int(d[-2:]) for d, _ in trend], [v for _, v in trend], marker="o")
    plt.title("Daily mean PM2.5, Adyar, October 2026"); plt.xlabel("Day of October"); plt.ylabel("PM2.5 (ug/m3)"); plt.grid(alpha=.3)
    plt.tight_layout(); plt.savefig("chart_trend.png", dpi=110)
    comp = con.execute("SELECT station, AVG(pm25) FROM readings WHERE day LIKE '2026-10%' GROUP BY station ORDER BY 2 DESC").fetchall()
    plt.figure(figsize=(8, 3.6)); plt.bar([s for s, _ in comp], [v for _, v in comp])
    plt.title("Mean PM2.5 by station, October 2026"); plt.ylabel("PM2.5 (ug/m3)"); plt.xticks(rotation=40, ha="right")
    plt.tight_layout(); plt.savefig("chart_stations.png", dpi=110)
    sc = con.execute("SELECT AVG(temp_c), AVG(pm25) FROM readings GROUP BY station, day").fetchall()
    plt.figure(figsize=(6, 4)); plt.scatter([t for t, _ in sc], [p for _, p in sc], s=4, alpha=.4)
    plt.title("Daily temperature vs PM2.5 (12 stations, 2026)"); plt.xlabel("Mean temperature (C)"); plt.ylabel("Mean PM2.5 (ug/m3)")
    plt.tight_layout(); plt.savefig("chart_scatter.png", dpi=110)
    r = statistics.correlation([t for t, _ in sc], [p for _, p in sc])
    print(f"B1.4 charts written: chart_trend.png chart_stations.png chart_scatter.png  (temp-PM2.5 r = {r:.2f})")
