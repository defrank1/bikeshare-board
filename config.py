import time
import json


class BikeShareAPI:
    """Client for the Capitol Bikeshare GBFS API."""

    def __init__(self, config, requests):
        self.config = config
        self.requests = requests
        self.url = config['gbfs_status_url']
        self.retries = config['api_retries']
        self.station_ids = set(config['station_ids'])

    def fetch_station_status(self):
        """
        Fetch station_status.json and return a dict of:
            { station_id: { 'classic': int, 'ebike': int, 'docks': int } }
        for only the configured stations.

        Returns None on failure after retries.
        """
        for attempt in range(self.retries):
            try:
                print(f"Fetching bikeshare data (attempt {attempt + 1})...")
                response = self.requests.get(self.url)
                data = response.json()
                response.close()

                result = {}
                for station in data['data']['stations']:
                    sid = station['station_id']
                    if sid not in self.station_ids:
                        continue

                    classic = 0
                    ebike = 0
                    for vt in station.get('vehicle_types_available', []):
                        if vt['vehicle_type_id'] == '1':
                            classic = vt['count']
                        elif vt['vehicle_type_id'] == '2':
                            ebike = vt['count']

                    result[sid] = {
                        'classic': classic,
                        'ebike': ebike,
                        'docks': station.get('num_docks_available', 0),
                    }

                print(f"Got data for {len(result)} station(s)")
                return result

            except Exception as e:
                print(f"API error: {e}")
                if attempt < self.retries - 1:
                    time.sleep(2)

        print("All API retries failed")
        return None
