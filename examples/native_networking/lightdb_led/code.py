import board
import json
from digitalio import DigitalInOut
from digitalio import Direction
import ssl
import socketpool
import wifi

import golioth.golioth as Golioth

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

led0 = DigitalInOut(board.IO42)
led0.direction = Direction.OUTPUT
led1 = DigitalInOut(board.IO41)
led1.direction = Direction.OUTPUT


def connected(client):
    print("Connected to Golioth!")
    client.listen_lightdb_state_at_path("/led/#")


def disconnected(client):
    print("Disconnected from Golioth!")


def on_message(client, path, message):
    print("Change on lightdb path {0}: {1}".format(path, message))
    if path == "led/":
        data = json.loads(message)
        if data is not None:
            for k in data:
                v = data[k]
                if k == "0":
                    led0.value = v
                if k == "1":
                    led1.value = v


# secrets dictionary must contain 'ssid' and 'password' at a minimum
print("Connecting...")
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("IP address ", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)

golioth_client = Golioth.Client(
    secrets["psk_id"], secrets["psk"], pool, ssl.create_default_context())
golioth_client.on_connect = connected
golioth_client.on_disconnect = disconnected
golioth_client.on_lightdb_message = on_message

print("Connecting to Golioth...")
golioth_client.connect()

while True:
    try:
        golioth_client.loop()
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        print("Reconnecting...")
        wifi.radio.connect(secrets["ssid"], secrets["password"])
        golioth_client.connect()
        continue
