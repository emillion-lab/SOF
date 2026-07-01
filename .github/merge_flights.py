import json

all_flights = []
total = 0

for fname in ['page1.json', 'page2.json']:
    try:
        with open(fname) as f:
            d = json.load(f)
        flights = d.get('data', [])
        if flights:
            all_flights.extend(flights)
            total = max(total, d.get('pagination', {}).get('total', 0))
            print(f"{fname}: {len(flights)} flights")
        else:
            print(f"{fname}: no data — {str(d)[:100]}")
    except Exception as e:
        print(f"{fname}: error {e}")

# Deduplicate by flight iata + scheduled time
seen = set()
unique = []
for f in all_flights:
    key = ((f.get('flight') or {}).get('iata') or '') + str((f.get('arrival') or {}).get('scheduled') or '')
    if key not in seen:
        seen.add(key)
        unique.append(f)

# Sort by Sofia arrival time (UTC+3)
def sofia_h(f):
    s = (f.get('arrival') or {}).get('scheduled') or ''
    if not s: return '99:99'
    return f"{(int(s[11:13])+3)%24:02d}:{s[14:16]}"

unique.sort(key=sofia_h)

with open('flight-cache.json', 'w') as f:
    json.dump({"pagination": {"total": total, "count": len(unique)}, "data": unique}, f, ensure_ascii=False)

print(f"\nSaved {len(unique)} unique flights sorted by Sofia time")
hrs = {}
for fl in unique:
    s = (fl.get('arrival') or {}).get('scheduled') or ''
    if s: 
        h = (int(s[11:13])+3)%24
        hrs[h] = hrs.get(h,0)+1
for h in sorted(hrs):
    print(f"  {h:02d}:xx — {hrs[h]} flights {'█'*hrs[h]}")
