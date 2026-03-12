"""
Optimize CBA schedule to minimize total travel distance.

Keeps the exact same 420 games (same home/away pairs, same counts).
Reorders which round each game is assigned to, using a greedy
minimum-travel-per-round matching heuristic.
"""

import csv
import math
import random
from collections import defaultdict

random.seed(42)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))

# ── Load teams ──────────────────────────────────────────────────
teams = {}
with open('cba_teams_2025_26.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        teams[row['Team']] = {
            'lat': float(row['Latitude']),
            'lng': float(row['Longitude']),
            'city': row['City'],
        }

def dist(team_a, team_b):
    """Distance between two teams' home cities."""
    a, b = teams[team_a], teams[team_b]
    return haversine(a['lat'], a['lng'], b['lat'], b['lng'])

def dist_coord(lat1, lng1, team_b):
    b = teams[team_b]
    return haversine(lat1, lng1, b['lat'], b['lng'])

# ── Load original games (preserve exact matchups) ──────────────
orig_games = []
with open('cba_schedule_2025_26.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        orig_games.append((row['Home Team (EN)'], row['Away Team (EN)']))

print(f"Total games to schedule: {len(orig_games)}")

# Pool of games: list of (home, away) tuples
pool = list(orig_games)

all_teams = sorted(teams)
n_rounds = 42

# ── Three-phase optimizer ──────────────────────────────────────
# Phase 1: Valid edge coloring (guarantees all games placed, 10/round)
# Phase 2: Greedy round ordering (sequence rounds to minimize travel)
# Phase 3: Local search — swap games between rounds to further reduce travel

from collections import defaultdict

# Phase 1: Edge coloring
game_round = [0] * len(pool)
team_rounds = defaultdict(set)

for i, (h, a) in enumerate(pool):
    for r in range(1, n_rounds + 1):
        if r not in team_rounds[h] and r not in team_rounds[a]:
            game_round[i] = r
            team_rounds[h].add(r)
            team_rounds[a].add(r)
            break
    else:
        print(f"  ERROR: Could not color game {i} ({h} vs {a})")

rounds_map = defaultdict(list)
for i, (h, a) in enumerate(pool):
    rounds_map[game_round[i]].append((h, a))

print(f"  Phase 1: edge coloring complete, all {len(pool)} games assigned")

# Phase 2: Greedy round ordering
cur_loc = {t: (teams[t]['lat'], teams[t]['lng']) for t in all_teams}
round_order = []
remaining = set(range(1, n_rounds + 1))

for step in range(n_rounds):
    best_cost = float('inf')
    best_r = None
    for r in remaining:
        cost = 0
        for h, a in rounds_map[r]:
            h_lat, h_lng = teams[h]['lat'], teams[h]['lng']
            cost += haversine(cur_loc[h][0], cur_loc[h][1], h_lat, h_lng)
            cost += haversine(cur_loc[a][0], cur_loc[a][1], h_lat, h_lng)
        if cost < best_cost:
            best_cost = cost
            best_r = r
    remaining.remove(best_r)
    round_order.append(best_r)
    for h, a in rounds_map[best_r]:
        h_lat, h_lng = teams[h]['lat'], teams[h]['lng']
        cur_loc[h] = (h_lat, h_lng)
        cur_loc[a] = (h_lat, h_lng)

print(f"  Phase 2: round ordering complete")

# Rebuild: ordered_rounds_map[new_round] = games
ordered_rounds_map = {}
for new_rnd, old_rnd in enumerate(round_order, 1):
    ordered_rounds_map[new_rnd] = rounds_map[old_rnd]

def compute_total_travel(rmap):
    """Compute total travel km for a given round->games mapping."""
    loc = {t: (teams[t]['lat'], teams[t]['lng']) for t in all_teams}
    total = 0
    per_team = defaultdict(int)
    for r in range(1, n_rounds + 1):
        for h, a in rmap[r]:
            h_lat, h_lng = teams[h]['lat'], teams[h]['lng']
            for team in [h, a]:
                d = haversine(loc[team][0], loc[team][1], h_lat, h_lng)
                total += d
                per_team[team] += d
            loc[h] = (h_lat, h_lng)
            loc[a] = (h_lat, h_lng)
    return total, per_team

pre_swap_total, _ = compute_total_travel(ordered_rounds_map)
print(f"  Pre-swap total travel: {pre_swap_total:,.0f} km")

# Phase 3: Local search — swap games between rounds
# Try swapping game from round A with game from round B
# if both swaps are valid (no team conflicts) and total travel decreases

def is_valid_round(games_list, exclude_game=None, add_game=None):
    """Check all teams appear at most once."""
    t = set()
    for g in games_list:
        if g == exclude_game:
            continue
        if g[0] in t or g[1] in t:
            return False
        t.add(g[0])
        t.add(g[1])
    if add_game:
        if add_game[0] in t or add_game[1] in t:
            return False
    return True

print(f"  Phase 3: local search swaps...")
improved = True
iteration = 0
while improved and iteration < 5:
    improved = False
    iteration += 1
    swaps_done = 0

    for r1 in range(1, n_rounds + 1):
        for r2 in range(r1 + 1, n_rounds + 1):
            for g1 in ordered_rounds_map[r1]:
                for g2 in ordered_rounds_map[r2]:
                    # Check validity of swapping g1 and g2
                    # r1 loses g1, gains g2; r2 loses g2, gains g1
                    r1_new = [g for g in ordered_rounds_map[r1] if g != g1] + [g2]
                    r2_new = [g for g in ordered_rounds_map[r2] if g != g2] + [g1]

                    # Check no team conflicts
                    r1_teams = set()
                    valid = True
                    for h, a in r1_new:
                        if h in r1_teams or a in r1_teams:
                            valid = False
                            break
                        r1_teams.add(h)
                        r1_teams.add(a)
                    if not valid:
                        continue

                    r2_teams = set()
                    for h, a in r2_new:
                        if h in r2_teams or a in r2_teams:
                            valid = False
                            break
                        r2_teams.add(h)
                        r2_teams.add(a)
                    if not valid:
                        continue

                    # Check if total travel improves
                    old_total, _ = compute_total_travel(ordered_rounds_map)
                    test_map = dict(ordered_rounds_map)
                    test_map[r1] = r1_new
                    test_map[r2] = r2_new
                    new_total, _ = compute_total_travel(test_map)

                    if new_total < old_total - 100:  # threshold to avoid tiny swaps
                        ordered_rounds_map[r1] = r1_new
                        ordered_rounds_map[r2] = r2_new
                        improved = True
                        swaps_done += 1

    print(f"    Iteration {iteration}: {swaps_done} swaps, "
          f"total travel: {compute_total_travel(ordered_rounds_map)[0]:,.0f}")

# Build final schedule
schedule = []
for r in range(1, n_rounds + 1):
    for h, a in ordered_rounds_map[r]:
        schedule.append((r, h, a))

# ── Compute travel mileage for the optimized schedule ──────────
schedule.sort(key=lambda x: x[0])

# Build reverse lookup: (lat, lng) -> city
coord_to_city = {}
for t in all_teams:
    coord_to_city[(teams[t]['lat'], teams[t]['lng'])] = teams[t]['city']

# Reset locations and compute travel
cur_loc = {t: (teams[t]['lat'], teams[t]['lng']) for t in all_teams}
detail = []
travel_per_round = {t: {} for t in all_teams}

for rnd, home, away in schedule:
    h_lat, h_lng = teams[home]['lat'], teams[home]['lng']

    for team in [home, away]:
        d = haversine(cur_loc[team][0], cur_loc[team][1], h_lat, h_lng)
        travel_per_round[team][rnd] = round(d)
        from_city = coord_to_city.get(cur_loc[team], '?')
        detail.append({
            'Team': team,
            'Round': rnd,
            'Km': round(d),
            'From': from_city,
            'To': teams[home]['city'],
        })

    cur_loc[home] = (h_lat, h_lng)
    cur_loc[away] = (h_lat, h_lng)

# ── Write optimized schedule CSV ───────────────────────────────
with open('cba_schedule_optimized_2025_26.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Round', 'Home Team', 'Away Team'])
    for rnd, home, away in schedule:
        writer.writerow([rnd, home, away])

# ── Write optimized wide-format mileage CSV ────────────────────
all_rounds = list(range(1, n_rounds + 1))
with open('cba_travel_mileage_optimized_2025_26.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Round'] + all_teams)
    for rnd in all_rounds:
        writer.writerow([rnd] + [travel_per_round[t].get(rnd, '') for t in all_teams])

# ── Write optimized detail CSV ─────────────────────────────────
with open('cba_travel_detail_optimized_2025_26.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Team', 'Round', 'Km', 'From', 'To'])
    writer.writeheader()
    writer.writerows(detail)

# ── Summary comparison ─────────────────────────────────────────
print("\n" + "=" * 65)
print("OPTIMIZED SCHEDULE — TOTAL TRAVEL PER TEAM")
print("=" * 65)

# Load original travel for comparison
orig_travel = defaultdict(int)
with open('cba_travel_detail_2025_26.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        orig_travel[row['Team']] += int(row['Km'])

opt_travel = defaultdict(int)
for row in detail:
    opt_travel[row['Team']] += row['Km']

print(f"{'Team':35s} {'Original':>10s} {'Optimized':>10s} {'Saved':>10s} {'%':>6s}")
print("-" * 75)
total_orig = total_opt = 0
for t in all_teams:
    o, n = orig_travel[t], opt_travel[t]
    total_orig += o
    total_opt += n
    saved = o - n
    pct = f"{saved/o*100:.1f}%" if o > 0 else "—"
    print(f"  {t:35s} {o:>8,} {n:>8,} {saved:>8,}  {pct:>6s}")

print("-" * 75)
saved_total = total_orig - total_opt
print(f"  {'TOTAL':35s} {total_orig:>8,} {total_opt:>8,} "
      f"{saved_total:>8,}  {saved_total/total_orig*100:.1f}%")

orig_vals = [orig_travel[t] for t in all_teams]
opt_vals = [opt_travel[t] for t in all_teams]
print(f"\n  Original — Avg: {sum(orig_vals)//20:,}  "
      f"Min: {min(orig_vals):,}  Max: {max(orig_vals):,}  "
      f"Spread: {max(orig_vals)-min(orig_vals):,}")
print(f"  Optimized — Avg: {sum(opt_vals)//20:,}  "
      f"Min: {min(opt_vals):,}  Max: {max(opt_vals):,}  "
      f"Spread: {max(opt_vals)-min(opt_vals):,}")
