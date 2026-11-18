"""B2: adversarial files, SQL injection, sentiment failures, executemany vs execute."""
import csv, sqlite3, sys, time
sys.path.insert(0, "../B4")

def naive_load(path):                                    # B1 load_clean applied to a file
    with open(path, encoding="utf-8") as f:
        return [(r["station"], r["date"], float(r["pm25"])) for r in csv.DictReader(f)]

def robust_load(path):
    text = ""
    for enc in ("utf-8", "utf-16", "cp1252"):
        try:
            with open(path, encoding=enc, newline="") as f: text = f.read(); break
        except UnicodeError: continue
    if not text.strip(): raise ValueError("empty file")
    dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;\t")
    rows = list(csv.DictReader(text.splitlines(), dialect=dialect))
    missing = {"station", "date", "pm25"} - set(rows[0] if rows else [])
    if missing: raise ValueError(f"missing column(s) {sorted(missing)}")
    return [(r["station"], r["date"], float(r["pm25"])) for r in rows], enc, dialect.delimiter

print("1. Adversarial files")
for name in ["missing_column", "wrong_delimiter", "utf16", "latin1", "empty"]:
    p = f"bad_inputs/{name}.csv"
    try: a = naive_load(p)
    except Exception as e: a = f"{type(e).__name__}: {str(e)[:40]}"
    try: b = robust_load(p)
    except Exception as e: b = f"rejected: {e}"
    print(f"  {name:<16} naive -> {a}\n  {'':<16} fixed -> {b}")

con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE stations (name TEXT, area TEXT)")
con.executemany("INSERT INTO stations VALUES (?,?)", [("Adyar", "South"), ("St. Thomas' Mount", "South-West"), ("Guindy", "South")])
print("\n2. Station search with a quote character")
for name in ["St. Thomas' Mount", "x' OR '1'='1"]:
    q = "SELECT * FROM stations WHERE name = '" + name + "'"
    try: r = con.execute(q).fetchall()
    except sqlite3.Error as e: r = f"{type(e).__name__}: {e}"
    print(f"  + string : {q}\n             -> {r}")
    print(f"  ? holder : -> {con.execute('SELECT * FROM stations WHERE name = ?', (name,)).fetchall()}")

from sentiment import score, label
print("\n3. Sentiment scorer on hard sentences (my reading -> scorer)")
for text, mine in [("Great, more smoke, just what we needed.", "negative"),
                   ("It is not that the air is not clean.", "positive"),
                   ("The buses are fast but the air is dirty and the roads are broken.", "negative"),
                   ("Clean? No way, the park is full of plastic.", "negative"),
                   ("Never seen such good air, staff were not rude.", "positive")]:
    print(f"  {mine:<9}-> {label(text):<9}({score(text):+d}) {text}")

print("\n4. executemany vs execute in a loop")
for n in (10_000, 100_000):
    data = [("S", "2026-10-01", float(i)) for i in range(n)]
    for kind in ("execute loop", "executemany"):
        c = sqlite3.connect(":memory:"); c.execute("CREATE TABLE aq (s TEXT, d TEXT, p REAL)")
        t0 = time.perf_counter()
        if kind == "executemany": c.executemany("INSERT INTO aq VALUES (?,?,?)", data)
        else:
            for row in data: c.execute("INSERT INTO aq VALUES (?,?,?)", row)
        c.commit(); print(f"  n={n:>7,} {kind:<13} {time.perf_counter() - t0:.4f}s")
