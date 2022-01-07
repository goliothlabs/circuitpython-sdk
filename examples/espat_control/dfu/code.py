import time
import os
import board
import json
import busio
from digitalio import DigitalInOut
from digitalio import Direction
from adafruit_espatcontrol import adafruit_espatcontrol
import adafruit_espatcontrol.adafruit_espatcontrol_socket as socket

import golioth.golioth as Golioth

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


def connected(client):
    print("Connected to Golioth!")
    client.listen_desired_version()


def disconnected(client):
    print("Disconnected from Golioth!")


def on_new_version(client, pkg, version, digest):
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


def on_download_artifact(client, pkg, version, payload):
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
golioth_client.on_desired_version_changed = on_new_version
golioth_client.on_download_artifact = on_download_artifact

print("Connecting to Golioth...")
golioth_client.connect()


while True:
    try:
        golioth_client.loop()
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
