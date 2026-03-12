import csv
from collections import Counter, defaultdict

# Load schedule
games = []
with open('cba_schedule_2025_26.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        games.append({
            'round': int(row['Round']),
            'home': row['Home Team (EN)'],
            'away': row['Away Team (EN)'],
        })

# Load teams with divisions
teams_div = {}
with open('cba_teams_2025_26.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        teams_div[row['Team']] = row['Division']

# Load travel detail
travel = defaultdict(int)
with open('cba_travel_detail_2025_26.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        travel[row['Team']] += int(row['Km'])

# ---- 1. Total travel per team ----
print("=" * 60)
print("TOTAL SEASON TRAVEL (km) - sorted highest to lowest")
print("=" * 60)
for t, m in sorted(travel.items(), key=lambda x: -x[1]):
    print(f"  {t:35s} {m:>7,}  ({teams_div[t]})")

vals = list(travel.values())
print(f"\n  Average: {sum(vals)//len(vals):,}   "
      f"Min: {min(vals):,}   Max: {max(vals):,}   "
      f"Spread: {max(vals)-min(vals):,}")

# ---- 2. Matchup counts (how many times each pair plays) ----
print("\n" + "=" * 60)
print("MATCHUP FREQUENCY ANALYSIS")
print("=" * 60)

matchup_count = Counter()
for g in games:
    pair = tuple(sorted([g['home'], g['away']]))
    matchup_count[pair] += 1

freq_dist = Counter(matchup_count.values())
for n_games, n_pairs in sorted(freq_dist.items()):
    print(f"  {n_pairs:3d} pairs play {n_games} times")

# Check intra-division vs inter-division
intra = []
inter = []
for (a, b), cnt in matchup_count.items():
    if teams_div[a] == teams_div[b]:
        intra.append((a, b, cnt))
    else:
        inter.append((a, b, cnt))

print(f"\n  Intra-division pairs: {len(intra)}")
for a, b, c in sorted(intra, key=lambda x: -x[2])[:10]:
    print(f"    {a:30s} vs {b:30s} = {c} games")

print(f"\n  Inter-division pairs: {len(inter)}")
for a, b, c in sorted(inter, key=lambda x: -x[2])[:10]:
    print(f"    {a:30s} vs {b:30s} = {c} games")

# ---- 3. Home/Away consecutive runs ----
print("\n" + "=" * 60)
print("LONGEST ROAD TRIP PER TEAM (consecutive away games)")
print("=" * 60)

all_teams = sorted(teams_div.keys())
games_sorted = sorted(games, key=lambda g: g['round'])

for team in all_teams:
    team_games = [(g['round'], 'H' if g['home'] == team else 'A')
                  for g in games_sorted if team in (g['home'], g['away'])]
    max_away = 0
    cur_away = 0
    for rnd, ha in team_games:
        if ha == 'A':
            cur_away += 1
            max_away = max(max_away, cur_away)
        else:
            cur_away = 0
    home_games = sum(1 for _, ha in team_games if ha == 'H')
    away_games = sum(1 for _, ha in team_games if ha == 'A')
    print(f"  {team:35s} H:{home_games:2d} A:{away_games:2d}  "
          f"Longest road trip: {max_away} games")

# ---- 4. Division-based travel comparison ----
print("\n" + "=" * 60)
print("TRAVEL BY DIVISION")
print("=" * 60)
for div in ['Northern', 'Southern']:
    div_teams = [t for t, d in teams_div.items() if d == div]
    div_miles = [travel[t] for t in div_teams]
    print(f"  {div}: avg {sum(div_miles)//len(div_miles):,} km  "
          f"(min {min(div_miles):,}, max {max(div_miles):,})")
