import time
import board
import busio
from digitalio import DigitalInOut
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
    client.listen_hello()

    client.log_debug("device connected from CircuitPython")
    client.log_info({
        'msg': "connected",
        'module': "espAT",
        'espATVersion': esp.version
    })


def disconnected(client):
    print("Disconnected from Golioth!")


def on_hello(client, message):
    print(message)


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
golioth_client.on_hello = on_hello

print("Connecting to Golioth...")
golioth_client.connect()

last_check = 0
i = 1
while True:
    try:
        golioth_client.loop()
        now = time.monotonic()
        if now - last_check > 5:
            golioth_client.log_debug("Hello "+str(i))
            i = i + 1
            last_check = now

    except (ValueError, RuntimeError, adafruit_espatcontrol.OKError) as e:
        print("Failed to get data, retrying\n", e)
        print("Resetting ESP module")
        esp.hard_reset()
        esp.connect(secrets)
        golioth_client.connect()
        continue
