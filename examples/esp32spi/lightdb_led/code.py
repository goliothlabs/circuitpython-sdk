import board
import busio
import board
import digitalio
import json
from digitalio import DigitalInOut
from digitalio import Direction
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi

import golioth.golioth as Golioth

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

led0 = DigitalInOut(board.GP14)
led0.direction = Direction.OUTPUT
led1 = DigitalInOut(board.GP15)
led1.direction = Direction.OUTPUT

# Change the Debug Flag if you have issues with AT commands
debugflag = False

esp32_cs = digitalio.DigitalInOut(board.GP21)
esp32_ready = digitalio.DigitalInOut(board.GP9)
esp32_reset = digitalio.DigitalInOut(board.GP7)

spi = busio.SPI(clock=board.GP22,MOSI=board.GP23,MISO=board.GP20)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)


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


print("Resetting ESP module")
esp.reset()
print("Connected to AT software version", esp.firmware_version.decode())

# secrets dictionary must contain 'ssid' and 'password' at a minimum
print("Connecting...")
esp.connect(secrets)
print("IP address", esp.pretty_ip(esp.ip_address))

Golioth.set_socket(socket, esp)
golioth_client = Golioth.Client(secrets["psk_id"], secrets["psk"])
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
        print("Resetting ESP module")
        esp.reset()
        esp.connect(secrets)
        golioth_client.connect()
        continue
