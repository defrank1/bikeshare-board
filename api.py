"""
Capitol Bikeshare LED Board
Displays real-time bike and dock availability for nearby CaBi stations
on a 64x32 RGB LED matrix using an Adafruit Matrix Portal.

Based on the dc-metro sign project by erikrrodriguez/metro-sign.
"""

import time
import board
import busio
import displayio
import framebufferio
import rgbmatrix
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests
import ssl

from config import config
from api import BikeShareAPI

# ---------------------------------------------------------------------------
# Color palette indices (used for the display bitmap)
# ---------------------------------------------------------------------------
COLOR_BG = 0
COLOR_HEADER = 1
COLOR_STATION = 2
COLOR_CLASSIC = 3
COLOR_EBIKE = 4
COLOR_DOCK = 5
COLOR_LOADING = 6

NUM_COLORS = 7

# ---------------------------------------------------------------------------
# Display setup
# ---------------------------------------------------------------------------
displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=config['matrix_width'],
    height=config['matrix_height'],
    bit_depth=4,
    rgb_pins=[
        board.MTX_R1, board.MTX_G1, board.MTX_B1,
        board.MTX_R2, board.MTX_G2, board.MTX_B2,
    ],
    addr_pins=[
        board.MTX_ADDR_A, board.MTX_ADDR_B,
        board.MTX_ADDR_C, board.MTX_ADDR_D,
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE,
)

display = framebufferio.FramebufferDisplay(matrix, auto_refresh=True)

# Create the full-screen bitmap and color palette
bitmap = displayio.Bitmap(config['matrix_width'], config['matrix_height'], NUM_COLORS)
palette = displayio.Palette(NUM_COLORS)
palette[COLOR_BG] = 0x000000
palette[COLOR_HEADER] = config['header_color']
palette[COLOR_STATION] = config['station_name_color']
palette[COLOR_CLASSIC] = config['classic_color']
palette[COLOR_EBIKE] = config['ebike_color']
palette[COLOR_DOCK] = config['dock_color']
palette[COLOR_LOADING] = config['loading_color']

tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
group = displayio.Group()
group.append(tile_grid)
display.root_group = group

# ---------------------------------------------------------------------------
# Font rendering helpers
# ---------------------------------------------------------------------------
font = config['font']
FONT_ASCENT = config['font_ascent']
MATRIX_W = config['matrix_width']
MATRIX_H = config['matrix_height']
PLUS_GAP = config['plus_extra_gap']


def clear_bitmap():
    """Set all pixels to background color."""
    for y in range(MATRIX_H):
        for x in range(MATRIX_W):
            bitmap[x, y] = COLOR_BG


def draw_text(text, x, y, color_idx):
    """
    Draw text onto the bitmap at pixel position (x, y).
    Inserts an extra pixel gap after '+' for readability.
    Returns the x position after the last character.
    """
    for ch in text:
        glyph = font.get_glyph(ord(ch))
        if glyph:
            y_off = FONT_ASCENT - glyph.height - glyph.dy
            for cy in range(glyph.height):
                for cx in range(glyph.width):
                    if glyph.bitmap[cx, cy]:
                        px = x + glyph.dx + cx
                        py = y + y_off + cy
                        if 0 <= px < MATRIX_W and 0 <= py < MATRIX_H:
                            bitmap[px, py] = color_idx
            x += glyph.shift_x
        if ch == '+':
            x += PLUS_GAP
    return x


def draw_text_right(text, right_x, y, color_idx):
    """Draw text right-aligned so the last pixel ends at right_x."""
    width = 0
    for ch in text:
        glyph = font.get_glyph(ord(ch))
        if glyph:
            width += glyph.shift_x
    draw_text(text, right_x - width, y, color_idx)


def clear_region(x1, y1, x2, y2):
    """Clear a rectangular region to background."""
    for y in range(max(0, y1), min(MATRIX_H, y2)):
        for x in range(max(0, x1), min(MATRIX_W, x2)):
            bitmap[x, y] = COLOR_BG


# ---------------------------------------------------------------------------
# Screen rendering
# ---------------------------------------------------------------------------
def draw_header():
    """Draw the static header row: STATN  C  E  D"""
    y = config['header_y']
    draw_text('STATN', 0, y, COLOR_HEADER)
    draw_text_right('C', config['classic_right_x'], y, COLOR_HEADER)
    draw_text_right('E', config['ebike_right_x'], y, COLOR_HEADER)
    draw_text_right('D', config['dock_right_x'], y, COLOR_HEADER)


def draw_loading():
    """Draw loading screen."""
    clear_bitmap()
    draw_header()
    y = config['row_y_positions'][1]  # Middle row
    draw_text(config['loading_text'], 0, y, COLOR_LOADING)


def draw_station_data(station_data):
    """
    Draw all station rows with live data.
    station_data: dict from api.fetch_station_status(), or None.
    """
    clear_bitmap()
    draw_header()

    station_ids = config['station_ids']
    station_names = config['station_names']
    row_ys = config['row_y_positions']

    for i in range(config['num_stations']):
        y = row_ys[i]
        name = station_names[i]

        # Draw station name
        draw_text(name, config['station_name_x'], y, COLOR_STATION)

        if station_data and station_ids[i] in station_data:
            data = station_data[station_ids[i]]
            draw_text_right(str(data['classic']), config['classic_right_x'], y, COLOR_CLASSIC)
            draw_text_right(str(data['ebike']), config['ebike_right_x'], y, COLOR_EBIKE)
            draw_text_right(str(data['docks']), config['dock_right_x'], y, COLOR_DOCK)
        else:
            # Show dashes if data unavailable
            draw_text_right('--', config['classic_right_x'], y, COLOR_CLASSIC)
            draw_text_right('--', config['ebike_right_x'], y, COLOR_EBIKE)
            draw_text_right('--', config['dock_right_x'], y, COLOR_DOCK)


# ---------------------------------------------------------------------------
# WiFi setup
# ---------------------------------------------------------------------------
print("Setting up WiFi...")
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_busy = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_busy, esp32_reset)

requests.set_socket(socket, esp)

# Show loading screen while connecting
draw_loading()

print(f"Connecting to {config['wifi_ssid']}...")
while not esp.is_connected:
    try:
        esp.connect_AP(config['wifi_ssid'], config['wifi_password'])
    except RuntimeError as e:
        print(f"WiFi connection failed: {e}, retrying...")
        time.sleep(2)

print(f"Connected! IP: {esp.pretty_ip(esp.ip_address)}")

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
api = BikeShareAPI(config, requests)

while True:
    station_data = api.fetch_station_status()
    draw_station_data(station_data)

    if station_data:
        for sid in config['station_ids']:
            name_idx = config['station_ids'].index(sid)
            name = config['station_names'][name_idx]
            if sid in station_data:
                d = station_data[sid]
                print(f"  {name}: C={d['classic']} E={d['ebike']} D={d['docks']}")
            else:
                print(f"  {name}: no data")

    time.sleep(config['refresh_interval'])
