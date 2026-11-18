"""A1: inspect a raw station file, create the SQLite design, compare CSV scan vs SQL."""
import csv, os, sqlite3, time
import pandas as pd
from gen_data import write_csv

print("A1.1 problems found in station_adyar_raw.csv")
seen = set()
with open("station_adyar_raw.csv", encoding="utf-8") as f:
    for n, row in enumerate(csv.DictReader(f), start=2):
        key = tuple(row.values())
        probs = []
        if key in seen: probs.append("duplicate row")
        seen.add(key)
        if row["station"] != row["station"].strip().title(): probs.append("station name case/spaces")
        if "/" in row["date"]: probs.append("date not YYYY-MM-DD")
        pm = row["pm25"]
        if pm == "": probs.append("pm25 missing (blank)")
        elif pm == "NA": probs.append("pm25 'NA'")
        elif float(pm) < 0: probs.append("pm25 negative")
        elif float(pm) > 999: probs.append("pm25 impossible (>999)")
        if not row["pm10"].replace(".", "").isdigit(): probs.append("pm10 not a number")
        if float(row["temp"]) > 60: probs.append("temperature in Fahrenheit")
        print(f"  line {n}: {', '.join(probs) or 'ok'}")

SCHEMA = """
CREATE TABLE stations (station_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE readings (station_id INTEGER NOT NULL REFERENCES stations(station_id),
                       day TEXT NOT NULL, hour INTEGER NOT NULL,
                       pm25 REAL, pm10 REAL, temp_c REAL,
                       PRIMARY KEY (station_id, day, hour));
"""
print("\nA1.2 schema:", SCHEMA)

if not os.path.exists("year_12.csv"):
    write_csv("year_12.csv", 12)

def num(x):
    try:
        v = float(x)
        return v if 0 <= v <= 999 else None
    except ValueError:
        return None

con = sqlite3.connect("aq.db")
con.executescript("DROP TABLE IF EXISTS readings; DROP TABLE IF EXISTS stations;" + SCHEMA)
ids = {}
with open("year_12.csv", encoding="utf-8") as f:
    data = []
    for r in csv.DictReader(f):
        sid = ids.setdefault(r["station"], len(ids) + 1)
        data.append((sid, r["date"], int(r["hour"]), num(r["pm25"]), num(r["pm10"]),
                     round((float(r["temp_f"]) - 32) * 5 / 9, 1)))
con.executemany("INSERT INTO stations VALUES (?, ?)", [(v, k) for k, v in ids.items()])
con.executemany("INSERT INTO readings VALUES (?,?,?,?,?,?)", data)
con.commit()

def csv_q1():
    s = c = 0
    with open("year_12.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["station"] == "Adyar" and r["date"].startswith("2026-10"):
                v = num(r["pm25"])
                if v is not None: s += v; c += 1
    return round(s / c, 2)
def csv_q2():
    best = {}
    with open("year_12.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["date"] == "2026-11-05":
                v = num(r["pm25"])
                if v is not None and v > best.get(r["station"], -1): best[r["station"]] = v
    return max(best, key=best.get)
def csv_q3():
    days = {}
    with open("year_12.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["station"] == "Guindy":
                v = num(r["pm25"])
                if v is not None: days.setdefault(r["date"], []).append(v)
    return sum(1 for v in days.values() if sum(v) / len(v) > 60)

Q = ["SELECT ROUND(AVG(pm25),2) FROM readings JOIN stations USING(station_id) WHERE name='Adyar' AND day LIKE '2026-10%'",
     "SELECT name FROM readings JOIN stations USING(station_id) WHERE day='2026-11-05' ORDER BY pm25 DESC LIMIT 1",
     "SELECT COUNT(*) FROM (SELECT day FROM readings JOIN stations USING(station_id) WHERE name='Guindy' GROUP BY day HAVING AVG(pm25)>60)"]
def pandas_q1():
    df = pd.read_csv("year_12.csv", na_values=["NA"])
    df = df[(df.pm25 >= 0) & (df.pm25 <= 999)]
    return round(df[(df.station == "Adyar") & df.date.str.startswith("2026-10")].pm25.mean(), 2)

def t(fn):
    t0 = time.perf_counter(); r = fn(); return r, time.perf_counter() - t0
print("A1.3 three questions, 12 stations x 1 year =", len(data), "rows")
print(f"{'question':<34}{'CSV scan':>18}{'SQL':>22}")
for name, fc, q in zip(["avg PM2.5 Adyar in October", "worst station on 2026-11-05", "Guindy days with daily avg > 60"],
                       [csv_q1, csv_q2, csv_q3], Q):
    rc, tc = t(fc); rs, ts = t(lambda: con.execute(q).fetchone()[0])
    print(f"{name:<34}{str(rc):>10} {tc:6.3f}s{str(rs):>14} {ts:6.4f}s")
rp, tp = t(pandas_q1)
print(f"pandas read_csv + filter for Q1: {rp}  {tp:.3f}s per question (reload each time)")
print(f"disk: CSV {os.path.getsize('year_12.csv') / 1e6:.1f} MB, SQLite {os.path.getsize('aq.db') / 1e6:.1f} MB")
con.close()
