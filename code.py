import time, ssl, json, socketpool, wifi, os
import board, busio, displayio
from adafruit_st7789 import ST7789
from adafruit_display_text import label
import adafruit_requests
import wireless
import terminalio
import adafruit_imageload

try:
    from fourwire import FourWire
except ImportError:
    from displayio import FourWire
    
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 240

mosi_pin = board.GP11
clk_pin = board.GP10
reset_pin = board.GP12
cs_pin = board.GP9
dc_pin = board.GP8

# Define color constants
COLOR_RED = 0xff0000
COLOR_GREEN = 0x8bbe1b
COLOR_YELLOW = 0xffae42
COLOR_ORANGE = 0xffa500
COLOR_BLACK = 0x000000
COLOR_WHITE = 0xf8f8ff

# Measurement Colors
COLORS = {
    4: COLOR_RED,
    1: COLOR_GREEN,
    2: COLOR_YELLOW,
    3: COLOR_ORANGE,
}
    
def mg_dl_to_mmol_l(mg_dl):
    mmol_l = mg_dl / 18.01559
    return round(mmol_l, 2)
    
def get_api_token():
    try:
        response = requests.post(LOG_IN_URL, headers=LOGIN_HEADERS, data=json_auth_params)
        response_as_json = response.json()
        data = response_as_json['data']
        response.close()
        print("Login success, received API token: " + str(data['authTicket']['token']))
        return data['authTicket']['token']
    except:
        print("unable to fetch API, check username and password")
        response.close()
        return "no_api_key"

def fetch_glucose_data():
    try:
        response = requests.get(CONNECTIONS_URL, headers=HEADERS)
        if response.status_code != 200:
            return(False, [])
        else:
            response_as_json = response.json()
            data = response_as_json['data']
            glucose_value = (data[0]['glucoseMeasurement']["Value"])
            timestamp = (data[0]['glucoseMeasurement']["Timestamp"])
            trend = (data[0]['glucoseMeasurement']["TrendArrow"])
            measurement_color = (data[0]['glucoseMeasurement']["MeasurementColor"])
            glucose_units = (data[0]['glucoseMeasurement']["GlucoseUnits"])
            target_low = (data[0]['targetLow'])
            target_high = (data[0]['targetHigh'])
            response.close()
            return (True, glucose_value, timestamp, trend, measurement_color, glucose_units, target_low, target_high)
    except:
        print("error")

    
def update_display(glucose_info):
    if glucose_info[4] == 0:
        glucose_units_label.text = "mmol/l"
    else:
        glucose_units_label.text = "mg/dL"
    glucose_value.color = COLORS.get(glucose_info[3])
    glucose_value.text = str(glucose_info[0])
    timestamp_label.text = "Last updated: " + str(glucose_info[1])
    low_value_label.text = str(glucose_info[5])
    high_value_label.text = str(glucose_info[6])
    if glucose_info[2] == 1: # straight down arrow
        trend_arrows[0] = 3
    elif glucose_info[2] == 2: #trending down arrow
        trend_arrows[0] = 1
    elif glucose_info[2] == 3: #level arrow
        trend_arrows[0] = 0
    elif glucose_info[2] == 4: # trending up arrow
        trend_arrows[0] = 2
    else: # straigh up arrow
        trend_arrows[0] = 4

while not wireless.wifi.radio.connected:
    wireless.connect()
    
print("Connected to WiFi")

pool = wireless.socketpool.SocketPool(wireless.wifi.radio)

# API endpoint URL
BASE_URL = "https://api.libreview.io"

LOG_IN_URL = BASE_URL + "/llu/auth/login"
CONNECTIONS_URL = BASE_URL + "/llu/connections"

#API_URL = "https://api.libreview.io/llu/connections"

auth_params = {
    'email': os.getenv('API_USER'),
    'password': os.getenv('API_PASSWORD')
}

# Serialize the payload to JSON format
json_auth_params = json.dumps(auth_params)

LOGIN_HEADERS = {
    'Content-type': 'application/json',
    'product': 'llu.android',
    'version': '4.7',
}

requests = adafruit_requests.Session(pool, ssl.create_default_context())

api_token = get_api_token()

HEADERS = {
    'Content-type': 'application/json',
    'product': 'llu.android',
    'version': '4.7',
    'Authorization': 'Bearer ' + api_token
}

font = terminalio.FONT

# mgdL label
glucose_units_label = label.Label(font, color=COLOR_WHITE)
glucose_units_label.anchor_point = (0.5, 0.0) #anchor middle top
glucose_units_label.anchored_position = (DISPLAY_WIDTH / 2, 130)
glucose_units_label.scale = (2)

# Create glucose_value label
glucose_value = label.Label(font, color=COLOR_WHITE)
glucose_value.anchor_point = (0.5, 0.0) #anchor middle top
glucose_value.anchored_position = (DISPLAY_WIDTH / 2, 5)
glucose_value.scale = (12)

# Create info label
info_label = label.Label(font, color=COLOR_WHITE)
info_label.anchor_point = (0.0, 0.0)
info_label.anchored_position = (5, 5)
info_label.scale = (1)

# Create timestamp label
timestamp_label = label.Label(font, color=COLOR_WHITE)
timestamp_label.anchor_point = (0.5, 1.0) #anchor middle bottom
timestamp_label.anchored_position = (DISPLAY_WIDTH / 2, DISPLAY_HEIGHT)
timestamp_label.scale = (1)

# Create MIN target label
low_label = label.Label(font, color=COLOR_GREEN, text="TARGET LOW")
low_label.anchor_point = (0.0, 0.0) #anchor left top
low_label.anchored_position = (20, 150)
low_label.scale = (1)

# Create MIN target value label
low_value_label = label.Label(font, color=COLOR_WHITE)
low_value_label.anchor_point = (0.0, 0.0) #anchor left top
low_value_label.anchored_position = (20, 162)
low_value_label.scale = (2)

# Create MAX target label
high_label = label.Label(font, color=COLOR_RED, text="TARGET HIGH")
high_label.anchor_point = (1.0, 0.0) #anchor right top
high_label.anchored_position = (DISPLAY_WIDTH - 20, 150)
high_label.scale = (1)

# Create MAX target value label
high_value_label = label.Label(font, color=COLOR_WHITE)
high_value_label.anchor_point = (1.0, 0.0) #anchor right top
high_value_label.anchored_position = (DISPLAY_WIDTH - 20, 162)
high_value_label.scale = (2)

    
displayio.release_displays()
spi = busio.SPI(clock=clk_pin, MOSI=mosi_pin)
while not spi.try_lock():
    pass
spi.configure(baudrate=24000000) # Configure SPI for 24MHz
spi.unlock()
display_bus = FourWire(spi, command=dc_pin, chip_select=cs_pin, reset=reset_pin)

display = ST7789(display_bus, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, rotation=270)

ui = displayio.Group(scale=1)
trend_arrow_group = displayio.Group(scale=4)
trend_arrow_group.x = 125
trend_arrow_group.y = 155
display.root_group = ui
ui.append(trend_arrow_group)

# Load the sprite sheet (bitmap)
sprite_sheet, palette = adafruit_imageload.load("/trend_arrows.bmp",
                                                bitmap=displayio.Bitmap,
                                                palette=displayio.Palette)

trend_arrows = displayio.TileGrid(sprite_sheet, pixel_shader=palette,
                            width = 1,
                            height = 1,
                            tile_width = 16,
                            tile_height = 16)


trend_arrow_group.append(trend_arrows)
ui.append(glucose_value)
ui.append(timestamp_label)
ui.append(glucose_units_label)
ui.append(info_label)
ui.append(low_label)
ui.append(high_label)
ui.append(low_value_label)
ui.append(high_value_label)

while True:
    (success, *glucose_info) = fetch_glucose_data()
    if not success:
        info_label.text = "Failed to read glucose data\nCheck username and password"
        print("Failed to read glucose data")
        time.sleep(300)
        continue
    
    if info_label.text != "":
        info_label.text = ""
    update_display(glucose_info)
    time.sleep(60)
