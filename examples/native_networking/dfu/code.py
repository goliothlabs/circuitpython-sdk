import os
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


# secrets dictionary must contain 'ssid' and 'password' at a minimum
print("Connecting...")
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("IP address ", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)

golioth_client = Golioth.Client(
    secrets["psk_id"], secrets["psk"], pool, ssl.create_default_context())
golioth_client.on_connect = connected
golioth_client.on_disconnect = disconnected
golioth_client.on_desired_version_changed = on_new_version
golioth_client.on_download_artifact = on_download_artifact

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
