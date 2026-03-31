import json

with open('all_deals.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print('Total deals:', d['total_deals'])

types = {}
for deal in d['deals']:
    t = deal.get('type', 'unknown')
    types[t] = types.get(t, 0) + 1

for t, count in sorted(types.items()):
    print(f'  {t}: {count}')