import csv
import math

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lng points."""
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# Load team home coordinates and cities
teams = {}
with open('cba_teams_2025_26.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        teams[row['Team']] = {
            'lat': float(row['Latitude']),
            'lng': float(row['Longitude']),
            'city': row['City'],
        }

# Load schedule
games = []
with open('cba_schedule_2025_26.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        games.append({
            'round': int(row['Round']),
            'date': row['Date'],
            'time': row['Time'],
            'home_team': row['Home Team (EN)'],
            'away_team': row['Away Team (EN)'],
        })

# Sort chronologically so travel is computed in actual game order
games.sort(key=lambda g: (g['date'], g['time']))

# For each team, walk through games chronologically and compute travel
all_teams = sorted(teams)
travel = {t: {} for t in all_teams}
detail = []  # long-format rows: team, round, km, from_city, to_city

for team in all_teams:
    cur_lat = teams[team]['lat']
    cur_lng = teams[team]['lng']
    cur_city = teams[team]['city']

    for g in games:
        if team not in (g['home_team'], g['away_team']):
            continue

        venue_team = g['home_team']
        venue_lat = teams[venue_team]['lat']
        venue_lng = teams[venue_team]['lng']
        venue_city = teams[venue_team]['city']

        dist = haversine(cur_lat, cur_lng, venue_lat, venue_lng)
        travel[team][g['round']] = round(dist)
        detail.append({
            'Team': team,
            'Round': g['round'],
            'Km': round(dist),
            'From': cur_city,
            'To': venue_city,
        })

        cur_lat = venue_lat
        cur_lng = venue_lng
        cur_city = venue_city

# Collect all rounds in order
all_rounds = sorted({g['round'] for g in games})

# Write output CSV — rows = rounds, columns = teams, values = km
with open('cba_travel_mileage_2025_26.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Round'] + all_teams)
    for rnd in all_rounds:
        writer.writerow([rnd] + [travel[t].get(rnd, '') for t in all_teams])

# Write detail CSV (long format with cities)
with open('cba_travel_detail_2025_26.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Team', 'Round', 'Km', 'From', 'To'])
    writer.writeheader()
    writer.writerows(detail)

print(f'Done — {len(all_rounds)} rounds x {len(all_teams)} teams\n'
      f'  cba_travel_mileage_2025_26.csv (wide format)\n'
      f'  cba_travel_detail_2025_26.csv  (long format with cities)')
