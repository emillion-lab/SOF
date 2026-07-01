import json, urllib.request, os
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("API_KEY", "")
if not API_KEY:
    print("No API_KEY"); exit(0)

BASE = f"http://api.aviationstack.com/v1/flights?access_key={API_KEY}&arr_iata=SOF&limit=100"

# Load existing cache to merge with
try:
    with open("flight-cache.json") as f:
        existing = json.load(f)
    existing_flights = existing.get("data", [])
    print(f"Existing cache: {len(existing_flights)} flights")
except:
    existing_flights = []

# Fetch new flights (current + upcoming)
new_flights = []
for offset in [0, 100]:
    try:
        req = urllib.request.Request(f"{BASE}&offset={offset}")
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read())
        fl = d.get("data", [])
        if not fl: break
        new_flights.extend(fl)
        print(f"offset={offset}: {len(fl)} flights")
    except Exception as e:
        print(f"offset={offset}: {e}"); break

# Merge: new flights override existing for same flight+time key
sofia_now = datetime.now(timezone(timedelta(hours=3)))
today = sofia_now.strftime("%Y-%m-%d")
cutoff = (sofia_now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")

def flight_key(f):
    iata = (f.get("flight") or {}).get("iata") or ""
    sched = (f.get("arrival") or {}).get("scheduled") or ""
    return iata + "|" + sched

# Start with existing, update with new
merged = {flight_key(f): f for f in existing_flights}
for f in new_flights:
    merged[flight_key(f)] = f  # new data overrides old

# Filter to today only and not too old
final = []
for f in merged.values():
    sched = (f.get("arrival") or {}).get("scheduled") or ""
    if not sched: continue
    date_part = sched[:10]
    # Keep today and tomorrow
    if date_part in [today, (sofia_now + timedelta(days=1)).strftime("%Y-%m-%d")]:
        final.append(f)

# Sort by Sofia arrival
def sofia_sort(f):
    s = (f.get("arrival") or {}).get("scheduled") or ""
    if not s: return "99:99"
    return f"{(int(s[11:13])+3)%24:02d}:{s[14:16]}"

final.sort(key=sofia_sort)

with open("flight-cache.json", "w") as f:
    json.dump({"pagination": {"count": len(final)}, "data": final}, f, ensure_ascii=False)

print(f"\nSaved {len(final)} flights for {today}")
hrs = {}
for fl in final:
    s = (fl.get("arrival") or {}).get("scheduled") or ""
    if s:
        h = (int(s[11:13])+3)%24
        hrs[h] = hrs.get(h,0)+1
for h in sorted(hrs):
    print(f"  {h:02d}:xx — {hrs[h]} {"█"*min(hrs[h],15)}")
