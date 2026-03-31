#!/usr/bin/env python3
"""
Capitol Bikeshare Station Finder

Run this on your computer (NOT on the Matrix Portal) to find CaBi station IDs
near your location. Then copy the station IDs into config.py on the board.

Usage:
    python3 station_finder.py                      # List all stations
    python3 station_finder.py --lat 38.9126 --lon -77.0418   # Sort by distance
    python3 station_finder.py --search "dupont"    # Search by name
"""

import json
import urllib.request
import argparse
import math

STATION_INFO_URL = 'https://gbfs.lyft.com/gbfs/2.3/dca-cabi/en/station_information.json'
STATION_STATUS_URL = 'https://gbfs.lyft.com/gbfs/2.3/dca-cabi/en/station_status.json'


def haversine(lat1, lon1, lat2, lon2):
    """Distance in meters between two lat/lon points."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def fetch_json(url):
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read())


def main():
    parser = argparse.ArgumentParser(description='Find Capitol Bikeshare stations')
    parser.add_argument('--lat', type=float, help='Your latitude (e.g. 38.9126)')
    parser.add_argument('--lon', type=float, help='Your longitude (e.g. -77.0418)')
    parser.add_argument('--search', type=str, help='Search station names (case-insensitive)')
    parser.add_argument('--limit', type=int, default=20, help='Number of results (default 20)')
    parser.add_argument('--status', action='store_true', help='Also show live bike/dock counts')
    args = parser.parse_args()

    print("Fetching station data...")
    info_data = fetch_json(STATION_INFO_URL)
    stations = info_data['data']['stations']

    status_map = {}
    if args.status:
        print("Fetching live status...")
        status_data = fetch_json(STATION_STATUS_URL)
        for s in status_data['data']['stations']:
            classic = 0
            ebike = 0
            for vt in s.get('vehicle_types_available', []):
                if vt['vehicle_type_id'] == '1':
                    classic = vt['count']
                elif vt['vehicle_type_id'] == '2':
                    ebike = vt['count']
            status_map[s['station_id']] = {
                'classic': classic,
                'ebike': ebike,
                'docks': s.get('num_docks_available', 0),
            }

    # Filter by search term
    if args.search:
        term = args.search.lower()
        stations = [s for s in stations if term in s['name'].lower()]
        if not stations:
            print(f"No stations matching '{args.search}'")
            return

    # Sort by distance if lat/lon provided
    if args.lat is not None and args.lon is not None:
        for s in stations:
            s['_dist'] = haversine(args.lat, args.lon, s['lat'], s['lon'])
        stations.sort(key=lambda s: s['_dist'])
    else:
        stations.sort(key=lambda s: s['name'])

    # Print results
    stations = stations[:args.limit]
    print(f"\n{'#':>3}  {'Station Name':<50} {'ID':<40} ", end='')
    if args.lat is not None:
        print(f"{'Dist':>7}", end='')
    if args.status:
        print(f"  {'C':>3} {'E':>3} {'D':>3}", end='')
    print()
    print("-" * 120)

    for i, s in enumerate(stations, 1):
        line = f"{i:>3}  {s['name']:<50} {s['station_id']:<40} "
        if args.lat is not None:
            dist = s['_dist']
            if dist < 1000:
                line += f"{dist:>5.0f}m "
            else:
                line += f"{dist/1000:>5.1f}km"
        if args.status and s['station_id'] in status_map:
            st = status_map[s['station_id']]
            line += f"  {st['classic']:>3} {st['ebike']:>3} {st['docks']:>3}"
        print(line)

    print(f"\nTotal: {len(stations)} station(s) shown")
    print("\nTo use a station, copy its ID into the 'station_ids' list in config.py")
    print("and add a 6-character abbreviation to the 'station_names' list.")
    print("\nAbbreviation rules:")
    print("  - Drop ordinal suffixes: 18th -> 18, 1st -> 1")
    print("  - Use + for intersections: 18th & R St NW -> 18+R")
    print("  - Short names for landmarks: Dupont Circle -> Dupont, Farragut Square -> FarSq")
    print("  - Max 6 characters recommended")


if __name__ == '__main__':
    main()
