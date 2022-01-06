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

led0 = DigitalInOut(board.GP14)
led0.direction = Direction.OUTPUT
led1 = DigitalInOut(board.GP15)
led1.direction = Direction.OUTPUT


def connected(client):
    print("Connected to Golioth!")
    client.listen_hello()
    client.listen_lightdb_state_at_path("/led/#")


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
            if k == "0":
                led0.value = v
            if k == "1":
                led1.value = v


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
