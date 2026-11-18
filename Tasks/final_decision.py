"""B4: lexicon scorer on 50 complaints, summariser, index on (station, day), scale estimate."""
import csv, os, re, sqlite3, sys, time
from collections import Counter
from sentiment import label

with open("complaints.csv", encoding="utf-8") as f:
    data = list(csv.DictReader(f))
pred = [label(r["text"]) for r in data]
agree = sum(p == r["label"] for p, r in zip(pred, data))
print(f"B4.1 scorer vs my labels on {len(data)} complaints: agree {agree}/{len(data)} = {100 * agree / len(data):.0f} %")
print("   confusion (mine -> scorer):", dict(Counter((r["label"], p) for p, r in zip(pred, data))))
print("   some disagreements:")
for p, r in [(p, r) for p, r in zip(pred, data) if p != r["label"]][:5]:
    print(f"     {r['label']:<8} -> {p:<8} {r['text']}")

STOP = set("the a an is and of in to near from it at on for every our we this was are my so be by has have not no".split())
def words(s): return [w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP]
texts = [r["text"] for r in data]
freq = Counter(w for t in texts for w in words(t))
print("\n   most frequent words:", freq.most_common(6))
top = sorted(texts, key=lambda t: -sum(freq[w] for w in words(t)))[:3]
print("   summary, most frequent words:"); [print("     -", t) for t in top]
print("   summary, first 3 sentences:"); [print("     -", t) for t in texts[:3]]

src = "../B3/year_120.csv" if os.path.exists("../B3/year_120.csv") else None
if src is None:
    from gen_data import write_csv; write_csv("year_120.csv", 120); src = "year_120.csv"
con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE r (station TEXT, day TEXT, hour INT, pm25 REAL)")
with open(src, encoding="utf-8") as f:
    con.executemany("INSERT INTO r VALUES (?,?,?,?)", ((r["station"], r["date"], int(r["hour"]),
                    float(r["pm25"]) if r["pm25"] not in ("", "NA") and float(r["pm25"]) >= 0 else None) for r in csv.DictReader(f)))
Q = "SELECT AVG(pm25) FROM r WHERE station = ? AND day = ?"
keys = [(f"Station{i:03d}", f"2026-{m:02d}-15") for i, m in zip(range(13, 113), [1 + i % 12 for i in range(100)])]
def run():
    t0 = time.perf_counter()
    for k in keys: con.execute(Q, k).fetchone()
    return (time.perf_counter() - t0) / len(keys)
print(f"\nB4.2 {con.execute('SELECT COUNT(*) FROM r').fetchone()[0]:,} rows, query: {Q}")
print("   plan before:", con.execute("EXPLAIN QUERY PLAN " + Q, keys[0]).fetchone()[-1])
before = run()
t0 = time.perf_counter(); con.execute("CREATE INDEX idx_station_day ON r(station, day)"); build = time.perf_counter() - t0
print("   plan after :", con.execute("EXPLAIN QUERY PLAN " + Q, keys[0]).fetchone()[-1])
after = run()
print(f"   per query: {before * 1000:.2f} ms without index, {after * 1000:.3f} ms with index ({before / after:.0f}x), index build {build:.2f}s")

print("\nB4.3 new scale: 220 stations x 96 readings/day")
per_month = 220 * 96 * 30
print(f"   {per_month:,} rows/month, {per_month * 12:,} rows/year (~{per_month * 12 * 40 / 1e9:.1f} GB at ~40 B/row incl. index)")
t0 = time.perf_counter(); [label(t) for t in texts * 1000]; tl = (time.perf_counter() - t0) / (len(texts) * 1000)
print(f"   lexicon scorer: {tl * 1e6:.1f} us/complaint -> 50,000 complaints in {tl * 50000:.2f}s")
