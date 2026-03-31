# Capitol Bikeshare LED Board

A real-time Capitol Bikeshare availability display for a 64x32 RGB LED matrix, built with CircuitPython 8 and an Adafruit Matrix Portal. Shows classic bike, ebike, and dock counts for three nearby stations.

Based on the [dc-metro sign](https://github.com/erikrrodriguez/dc-metro) project.

## Display Layout

```
STATN          C  E  D        (red header)
15+L           8  4  7        (orange / green / blue numbers)
6+O            2  2 11
Dupont         0  1 18
```

- **Station names**: orange
- **Classic bike counts (C)**: orange
- **Ebike counts (E)**: green
- **Dock counts (D)**: blue

No API key is needed — Capitol Bikeshare publishes free, public GBFS data.

## Hardware

Same hardware as the dc-metro sign:

- [Adafruit Matrix Portal](https://www.adafruit.com/product/4745) — $24.99
- 64x32 RGB LED Matrix ([3mm](https://www.adafruit.com/product/2279), [4mm](https://www.adafruit.com/product/2278), [5mm](https://www.adafruit.com/product/2277), or [6mm](https://www.adafruit.com/product/2276) pitch)
- USB-C power supply (15W+)
- USB-C cable

## Setup

### 1. Prepare the board

Follow the hardware assembly steps in the [dc-metro README](https://github.com/erikrrodriguez/dc-metro#part-1-prepare-the-board).

### 2. Flash CircuitPython

1. Connect the board via USB-C and double-click RESET.
2. Download [CircuitPython 8 for Matrix Portal M4](https://circuitpython.org/board/matrixportal_m4/).
3. Drag the `.uf2` file onto the MATRIXBOOT volume.
4. The board remounts as CIRCUITPY.

### 3. Install libraries

Copy the `lib/` folder from the [dc-metro repo](https://github.com/erikrrodriguez/dc-metro) (or decompress `lib.zip`) onto the CIRCUITPY volume. The same CircuitPython 8 libraries work for this project.

Make sure `lib/5x7.bdf` (the bitmap font) is included.

### 4. Copy source files

Copy the following files from this repo to the root of the CIRCUITPY volume:
- `code.py`
- `config.py`
- `api.py`

### 5. Configure

Open `config.py` on the CIRCUITPY volume and fill in:

1. Your WiFi SSID and password
2. (Optional) Your station IDs and abbreviations — defaults are set to three stations near Dupont Circle

### 6. Done

Save `config.py` and the board will restart, connect to WiFi, and begin showing live bikeshare data.

## Choosing Your Stations

Run the station finder on your computer (not on the board):

```bash
# Find the 10 closest stations to a location
python3 station_finder.py --lat 38.9126 --lon -77.0418 --limit 10

# Search by name
python3 station_finder.py --search "dupont"

# Show live counts too
python3 station_finder.py --lat 38.9126 --lon -77.0418 --status
```

Copy the station IDs from the output into `config.py`, and write a 6-character abbreviation for each.

**Abbreviation rules:**
- Drop ordinal suffixes: `18th` → `18`, `1st` → `1`
- Use `+` for intersections: `18th & R St NW` → `18+R`
- Short names for landmarks: `Dupont Circle` → `Dupont`, `Farragut Square` → `FarSq`
- The `+` character gets an automatic 1-pixel gap for readability

## Data Source

[Capitol Bikeshare GBFS Feed](https://gbfs.lyft.com/gbfs/2.3/dca-cabi/en/gbfs.json) (GBFS v2.3, hosted by Lyft)

- `station_status.json` — real-time bike/dock availability
- `station_information.json` — station names and locations
- `vehicle_types.json` — type `1` = classic bike, type `2` = ebike

## Off Hours (Optional)

To turn the display off at night, set up a free [Adafruit IO](https://learn.adafruit.com/adafruit-magtag/getting-the-date-time) account and fill in `aio_username` and `aio_key` in `config.py`. Then set your preferred on/off times.

## License

Same license as the original dc-metro project.
