import time
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


def connected(client):
    print("Connected to Golioth!")
    client.listen_hello()

    client.log_debug("device connected from CircuitPython")
    client.log_info({
        'msg': "connected",
        'module': "networking",
        'hostname': wifi.radio.hostname,
    })


def disconnected(client):
    print("Disconnected from Golioth!")


def on_hello(client, message):
    print(message)


# secrets dictionary must contain 'ssid' and 'password' at a minimum
print("Connecting...")
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("IP address ", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)

golioth_client = Golioth.Client(
    secrets["psk_id"], secrets["psk"], pool, ssl.create_default_context())
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

    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        print("Reconnecting...")
        wifi.radio.connect(secrets["ssid"], secrets["password"])
        golioth_client.connect()
        continue
