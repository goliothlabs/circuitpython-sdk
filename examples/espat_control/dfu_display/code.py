import time
import os
import board
import json
import busio
from digitalio import DigitalInOut
from digitalio import Direction
from adafruit_espatcontrol import adafruit_espatcontrol
import adafruit_espatcontrol.adafruit_espatcontrol_socket as socket

import displayio
import adafruit_imageload
from adafruit_st7735r import ST7735R

import golioth.golioth as Golioth

# Release any resources currently in use for the displays
displayio.release_displays()

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Change the Debug Flag if you have issues with AT commands
debugflag = False

RX = board.GP9
TX = board.GP8
resetpin = DigitalInOut(board.GP6)
rtspin = DigitalInOut(board.GP7)
uart = busio.UART(TX, RX, timeout=0.1)

led0 = DigitalInOut(board.GP14)
led0.direction = Direction.OUTPUT
led1 = DigitalInOut(board.GP15)
led1.direction = Direction.OUTPUT

tft_cs = board.GP16
tft_dc = board.GP17
tft_res = board.GP20
spi_mosi = board.GP3
spi_miso = board.GP4
spi_clk = board.GP2
spi = busio.SPI(spi_clk, MOSI=spi_mosi, MISO=spi_miso)
displayio.release_displays()
display_bus = displayio.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=tft_res)
display = ST7735R(display_bus, width=128, height=160, rotation=0, bgr=True)


def connected(client):
    print("Connected to Golioth!")
    client.listen_hello()
    client.listen_lightdb_state_at_path("/led/#")
    client.listen_desired_version()

    client.log_debug("device connected from CircuitPython")
    client.log_info(
        {"msg": "connected", "module": "espAT", "espATVersion": esp.version}
    )


def disconnected(client):
    print("Disconnected from Golioth!")


def hello(client, message):
    print(message)


def message(client, path, message):
    print("Change on lightdb path {0}: {1}".format(path, message))
    if path == "led/":
        data = json.loads(message)
        for k in data:
            v = data[k]
            print("found {0} -> {1}".format(k, v))
            if k == "0":
                led0.value = v
            if k == "1":
                led1.value = v


latest_image = ""


def show_latest_image():
    for f in os.listdir("/artifacts"):
        if f.startswith("emoji") and latest_image != f:
            parts = f.split("-")
            pkg = parts[0]
            version = "-".join(parts[1:])
            show_image(pkg, version)
            return f

    return latest_image


def show_image(pkg, version):
    fname = "/artifacts/" + pkg + "-" + version
    bitmap, palette = adafruit_imageload.load(
        fname, bitmap=displayio.Bitmap, palette=displayio.Palette
    )
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
    group = displayio.Group()
    group.append(tile_grid)
    display.show(group)


def new_version(client, pkg, version, digest):
    print("new version")
    print(pkg)
    print(version)
    print(digest)
    found = False
    fname = "/artifacts/" + pkg + "-" + version
    try:
        os.stat(fname)
        found = True
    except OSError as e:
        found = False

    if not found:
        print("triggering download")
        client.download_artifact(pkg, version)


def download_artifact(client, pkg, version, payload):
    print("file arrived")
    print(pkg)
    print(version)
    try:
        if "artifacts" not in os.listdir("/"):
            os.mkdir("artifacts")

        fname = pkg + "-" + version
        with open("/artifacts/" + fname, "w") as fp:
            fp.write(payload)
            fp.flush()

        for f in os.listdir("/artifacts"):
            if f.startswith(pkg) and f != fname:
                print("removing " + f)
                os.remove("/artifacts/" + f)

    except OSError as e:
        print("error saving artifact")
        print(e)


latest_image = show_latest_image()
print("ESP AT commands")
esp = adafruit_espatcontrol.ESP_ATcontrol(
    uart, 115200, reset_pin=resetpin, rts_pin=rtspin, debug=debugflag
)
print("Resetting ESP module")
esp.hard_reset()
print("Connected to AT software version ", esp.version)

# secrets dictionary must contain 'ssid' and 'password' at a minimum
print("Connecting...")
esp.connect(secrets)
print("IP address ", esp.local_ip)

Golioth.set_socket(socket, esp)
golioth_client = Golioth.Client(secrets["psk_id"], secrets["psk"])
golioth_client.on_connect = connected
golioth_client.on_disconnect = disconnected
golioth_client.on_hello = hello
golioth_client.on_lightdb_message = message
golioth_client.on_desired_version_changed = new_version
golioth_client.on_download_artifact = download_artifact

print("Connecting to Golioth...")
golioth_client.connect()

last_img_check = time.monotonic()
while True:
    try:
        now = time.monotonic()
        golioth_client.loop()
        if now - last_img_check > 1:
            latest_image = show_latest_image()
            last_img_check = now

    except (ValueError, RuntimeError, adafruit_espatcontrol.OKError) as e:
        print("Failed to get data, retrying\n", e)
        print("Resetting ESP module")
        esp.hard_reset()
        esp.connect(secrets)
        golioth_client.connect()
        continue
    except Exception as e:
        print("Unknown error\n", e)
        print("Resetting ESP module")
        esp.hard_reset()
        esp.connect(secrets)
        golioth_client.connect()
        continue
