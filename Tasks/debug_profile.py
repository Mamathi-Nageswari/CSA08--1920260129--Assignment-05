"""A4: debugging tools (print, assert, logging, pdb) and profiling (perf_counter, timeit, cProfile)."""
import cProfile, io, logging, pstats, random, statistics, sys, time, timeit

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(funcName)s: %(message)s", stream=sys.stdout)
log = logging.getLogger("clean")

def to_float(x):
    try: v = float(x)
    except ValueError:
        log.debug("not a number: %r", x); return None
    if not 0 <= v <= 999:
        log.warning("out of range: %s", v); return None
    return v

def clean(raw):
    out = [v for v in map(to_float, raw) if v is not None]
    assert all(0 <= v <= 999 for v in out), "cleaned value out of range"
    return out

def median_day(vals): return statistics.median(vals)

print("1. logging + assert on a small input:")
print("   result:", clean(["48", "NA", "-5", "1500", "60"]))
print("   (pdb: put breakpoint() inside to_float, then 'p x', 'n', 'c' to step through a bad value)")

logging.disable(logging.CRITICAL)                    # switch off for the big run
raw = [str(random.uniform(-10, 1100)) if random.random() > 0.02 else "NA" for _ in range(200_000)]

print("\n2. perf_counter for each stage:")
t0 = time.perf_counter(); c = clean(raw); t1 = time.perf_counter(); median_day(c); t2 = time.perf_counter()
print(f"   clean {t1 - t0:.4f}s   median {t2 - t1:.4f}s")
print("3. timeit to_float('48.5'):", f"{timeit.timeit(lambda: to_float('48.5'), number=100_000) * 10:.3f} us per call")
print("4. cProfile top 4 by total time:")
pr = cProfile.Profile(); pr.enable(); median_day(clean(raw)); pr.disable()
s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(4)
lines = s.getvalue().splitlines(); i = next(i for i, l in enumerate(lines) if "ncalls" in l)
print("\n".join(l.replace("/home/ubuntu/csa08_a5/A4/", "") for l in lines[i:i + 5]))

print("\nAlternative: cost of debug output on 200,000 lines")
class Null:
    def write(self, s): pass
    def flush(self): pass
null = Null()
def with_print(r):
    for x in r: print("value", x, file=null)
logging.disable(logging.NOTSET)
h = logging.StreamHandler(null); log2 = logging.getLogger("t"); log2.addHandler(h); log2.propagate = False
def with_logging(r, level):
    log2.setLevel(level)
    for x in r: log2.debug("value %s", x)
def nothing(r):
    for x in r: pass
for name, f in [("no debug", lambda: nothing(raw)), ("print()", lambda: with_print(raw)),
                ("logging on (DEBUG)", lambda: with_logging(raw, logging.DEBUG)),
                ("logging off (level WARNING)", lambda: with_logging(raw, logging.WARNING))]:
    t0 = time.perf_counter(); f(); print(f"   {name:<28}{time.perf_counter() - t0:.4f}s")
