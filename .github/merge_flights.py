import json, urllib.request, os
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get('API_KEY', '')
if not API_KEY:
    print("No API_KEY")
    exit(0)

BASE = f"http://api.aviationstack.com/v1/flights?access_key={API_KEY}&arr_iata=SOF&limit=100"

all_flights = []
total = 0

# Fetch 3 pages (300 flights) to cover full day
for offset in [0, 100, 200]:
    try:
        url = f"{BASE}&offset={offset}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read())
        flights = d.get('data', [])
        if not flights:
            print(f"offset={offset}: no data — {str(d)[:100]}")
            break
        all_flights.extend(flights)
        total = d.get('pagination', {}).get('total', total)
        print(f"offset={offset}: {len(flights)} flights (total: {total})")
    except Exception as e:
        print(f"offset={offset}: error {e}")
        break

# Filter only arrivals for today and tomorrow Sofia time
sofia_now = datetime.now(timezone(timedelta(hours=3)))
today = sofia_now.strftime('%Y-%m-%d')
tomorrow = (sofia_now + timedelta(days=1)).strftime('%Y-%m-%d')

today_flights = []
for f in all_flights:
    sched = (f.get('arrival') or {}).get('scheduled') or ''
    if not sched: continue
    date_part = sched[:10]
    if date_part in [today, tomorrow]:
        today_flights.append(f)

# If no today flights, keep all (maybe timezone issue)
if not today_flights:
    print(f"No flights for {today}/{tomorrow} — keeping all {len(all_flights)}")
    today_flights = all_flights

# Deduplicate
seen = set()
unique = []
for f in today_flights:
    key = ((f.get('flight') or {}).get('iata') or '') + str((f.get('arrival') or {}).get('scheduled') or '')
    if key not in seen:
        seen.add(key)
        unique.append(f)

# Sort by Sofia arrival time
def sofia_sort(f):
    s = (f.get('arrival') or {}).get('scheduled') or ''
    if not s: return '99:99'
    return f"{(int(s[11:13])+3)%24:02d}:{s[14:16]}"

unique.sort(key=sofia_sort)

with open('flight-cache.json', 'w') as f:
    json.dump({"pagination": {"total": total, "count": len(unique)}, "data": unique}, f, ensure_ascii=False)

print(f"\nSaved {len(unique)} flights for {today}")
hrs = {}
for fl in unique:
    s = (fl.get('arrival') or {}).get('scheduled') or ''
    if s:
        h = (int(s[11:13])+3)%24
        hrs[h] = hrs.get(h,0)+1
for h in sorted(hrs):
    print(f"  {h:02d}:xx — {hrs[h]} {'█'*hrs[h]}")
