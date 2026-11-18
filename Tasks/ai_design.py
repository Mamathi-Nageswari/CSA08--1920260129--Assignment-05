"""A5: lexicon sentiment with negation, extractive summariser, rule-based chatbot over SQLite."""
import re, sqlite3
from collections import Counter

POSITIVE = {"good", "clean", "fast", "helpful", "improved", "fresh", "better", "clear"}
NEGATIVE = {"bad", "dirty", "slow", "rude", "smoke", "broken", "dust", "worse", "burning", "smell"}
NEGATORS = {"not", "never", "no"}
STOP = {"the", "a", "is", "and", "of", "in", "to", "near", "from", "it", "at", "on", "for", "there", "every", "our", "we", "this", "was", "are"}

def score(text):
    words = re.findall(r"[a-z]+", text.lower())
    total = 0
    for i, w in enumerate(words):
        v = 1 if w in POSITIVE else -1 if w in NEGATIVE else 0
        if i and words[i - 1] in NEGATORS: v = -v
        total += v
    return total

def summarise(text, k=1):
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    freq = Counter(w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP)
    ranked = sorted(sents, key=lambda s: -sum(freq[w] for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP))
    keep = set(ranked[:k]); return " ".join(s for s in sents if s in keep)

con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE daily (station TEXT, day TEXT, pm25 REAL)")
con.executemany("INSERT INTO daily VALUES (?,?,?)", [("Adyar", "2026-11-18", 62.4), ("Guindy", "2026-11-18", 88.1), ("Adyar", "2026-11-17", 55.0)])
STATIONS = {"adyar": "Adyar", "guindy": "Guindy"}

def chatbot(question, today="2026-11-18"):
    q = question.lower()
    st = next((v for k, v in STATIONS.items() if k in q), None)
    if st is None: return "Sorry, I know only these stations: " + ", ".join(STATIONS.values())
    day = "2026-11-17" if "yesterday" in q else today
    if "pm2.5" in q or "pm25" in q or "air" in q:
        r = con.execute("SELECT pm25 FROM daily WHERE station=? AND day=?", (st, day)).fetchone()
        return f"PM2.5 in {st} on {day}: {r[0]} ug/m3" if r else f"No data for {st} on {day}"
    return "I can answer PM2.5 questions, e.g. 'What is the PM2.5 in Adyar today?'"

for c in ["The air is not bad today.", "Smoke from the factory, the road is dirty.", "Air is clean and fresh."]:
    print(f"{score(c):+d}  {c}")
text = ("There is smoke near the bus depot every morning. The smoke smell enters our homes. "
        "The road was cleaned last week. Children cough because of the smoke and dust.")
print("\nsummary:", summarise(text))
for q in ["What is the PM2.5 in Adyar today?", "air in guindy yesterday?", "Is Velachery air ok?", "Hello"]:
    print(f"Q: {q}\n   {chatbot(q)}")
