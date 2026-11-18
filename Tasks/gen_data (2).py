"""Generate one year of hourly readings (with missing/bad values) for n stations."""
import csv, random
from datetime import date, timedelta

NAMES = ["Adyar", "Guindy", "Velachery", "Alandur", "Perungudi", "Kodungaiyur",
         "Manali", "Royapuram", "Arumbakkam", "Ennore", "Tondiarpet", "Anna Nagar"]

def stations(n):
    return [NAMES[i] if i < len(NAMES) else f"Station{i + 1:03d}" for i in range(n)]

def rows(n_stations, days=365, seed=5):
    rnd = random.Random(seed)
    start = date(2026, 1, 1)
    for s_i, st in enumerate(stations(n_stations)):
        base = 30 + 4 * (s_i % 12)
        for d in range(days):
            day = (start + timedelta(d)).isoformat()
            season = 25 if d < 60 or d > 300 else 0
            for h in range(24):
                pm = round(rnd.gauss(base + season + (15 if 7 <= h <= 10 else 0), 12), 1)
                r = rnd.random()
                pm = "" if r < 0.02 else "NA" if r < 0.03 else (-abs(pm) if r < 0.035 else pm)
                temp_f = round(rnd.gauss(86 - season / 3, 4), 1)
                yield st, day, h, pm, round(pm * 1.8, 1) if isinstance(pm, float) and pm > 0 else 60, temp_f

def write_csv(path, n_stations, days=365):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["station", "date", "hour", "pm25", "pm10", "temp_f"])
        w.writerows(rows(n_stations, days))

if __name__ == "__main__":
    write_csv("year_12.csv", 12)
    print("year_12.csv written")
