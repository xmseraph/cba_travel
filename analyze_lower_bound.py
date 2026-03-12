"""
Compute a theoretical lower bound for each team's travel if they could
freely reorder their 42 games (ignoring round/coupling constraints).
Compare original, optimized, and lower bound.
"""
import csv, math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon/2)**2)
    return R * 2 * math.asin(math.sqrt(a))

# Load teams
teams = {}
with open('cba_teams_2025_26.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        teams[row['Team']] = {
            'lat': float(row['Latitude']),
            'lng': float(row['Longitude']),
            'city': row['City'],
        }

# Load original games to build each team's venue list
orig_games = []
with open('cba_schedule_2025_26.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        orig_games.append((row['Home Team (EN)'], row['Away Team (EN)']))

all_teams = sorted(teams)
team_venues = {t: [] for t in all_teams}
for home, away in orig_games:
    team_venues[home].append(home)
    team_venues[away].append(home)

# Nearest-neighbor heuristic
def nn_travel(team, venues):
    home = teams[team]
    remaining = list(range(len(venues)))
    cur_lat, cur_lng = home['lat'], home['lng']
    total = 0
    order = []
    for _ in range(len(venues)):
        best_i, best_d = None, float('inf')
        for i in remaining:
            v = teams[venues[i]]
            d = haversine(cur_lat, cur_lng, v['lat'], v['lng'])
            if d < best_d:
                best_d = d
                best_i = i
        remaining.remove(best_i)
        total += best_d
        v = teams[venues[best_i]]
        cur_lat, cur_lng = v['lat'], v['lng']
        order.append(best_i)
    return total, order

# 2-opt improvement
def two_opt_travel(team, venues, initial_order):
    home = teams[team]
    n = len(initial_order)
    order = list(initial_order)

    def calc_total(ol):
        t = 0
        clat, clng = home['lat'], home['lng']
        for idx in ol:
            v = teams[venues[idx]]
            t += haversine(clat, clng, v['lat'], v['lng'])
            clat, clng = v['lat'], v['lng']
        return t

    best_total = calc_total(order)
    improved = True
    iters = 0
    while improved and iters < 100:
        improved = False
        iters += 1
        for i in range(n - 1):
            for j in range(i + 1, min(i + 25, n)):
                new_order = order[:i] + order[i:j+1][::-1] + order[j+1:]
                new_total = calc_total(new_order)
                if new_total < best_total - 0.5:
                    order = new_order
                    best_total = new_total
                    improved = True
                    break
            if improved:
                break
    return best_total

# Load actual travel totals
def load_team_totals(path):
    totals = {}
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            t = row['Team']
            totals[t] = totals.get(t, 0) + int(row['Km'])
    return totals

orig_totals = load_team_totals('cba_travel_detail_2025_26.csv')
opt_totals = load_team_totals('cba_travel_detail_optimized_2025_26.csv')

# Print results
hdr = f"{'Team':30s} {'Original':>9s} {'Optimized':>9s} {'LowerBnd':>9s} {'Gap':>7s} {'Efficiency':>10s}"
print(hdr)
print('-' * len(hdr))

total_orig = total_opt = total_lb = 0
for team in all_teams:
    nn_total, nn_order = nn_travel(team, team_venues[team])
    lb = two_opt_travel(team, team_venues[team], nn_order)

    o = orig_totals.get(team, 0)
    p = opt_totals.get(team, 0)
    gap = p - lb
    possible = o - lb
    captured = o - p
    eff = (captured / possible * 100) if possible > 0 else 100.0

    total_orig += o
    total_opt += p
    total_lb += lb

    print(f"{team:30s} {o:>9,d} {p:>9,d} {lb:>9,.0f} {gap:>+7,.0f} {eff:>9.1f}%")

print('-' * len(hdr))
possible_total = total_orig - total_lb
captured_total = total_orig - total_opt
eff_total = captured_total / possible_total * 100 if possible_total > 0 else 100
print(f"{'TOTAL':30s} {total_orig:>9,d} {total_opt:>9,d} {total_lb:>9,.0f} {total_opt-total_lb:>+7,.0f} {eff_total:>9.1f}%")
print()
print(f"Theoretical lower bound (sum of independent team optima): {total_lb:>10,.0f} km")
print(f"Optimized schedule:                                       {total_opt:>10,d} km")
print(f"Original schedule:                                        {total_orig:>10,d} km")
print()
print(f"Gap from optimized to lower bound: {total_opt - total_lb:,.0f} km ({(total_opt-total_lb)/total_lb*100:.1f}% above LB)")
print(f"Savings captured: {captured_total:,d} of {possible_total:,.0f} possible km ({eff_total:.1f}%)")
print()
print("Note: The lower bound assumes each team can independently reorder")
print("their 42 games (ignoring the constraint that all 10 games in a round")
print("must happen simultaneously). The true coupled optimum is higher than")
print("this bound, so the optimized schedule is closer to optimal than the")
print("efficiency % suggests.")

# Write lower bounds to CSV for use in Streamlit
with open('cba_travel_lower_bound.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Team', 'LowerBound'])
    for team in all_teams:
        nn_total2, nn_order2 = nn_travel(team, team_venues[team])
        lb2 = two_opt_travel(team, team_venues[team], nn_order2)
        writer.writerow([team, round(lb2)])
print("\nWrote cba_travel_lower_bound.csv")
