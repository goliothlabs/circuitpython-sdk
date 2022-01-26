import json
import adafruit_minimqtt.adafruit_minimqtt as MQTT

GOLIOTH_MQTT_HOST = "mqtt.golioth.io"
GOLIOTH_MQTT_PORT = const(8883)

LIGHTDB_STATE_PREFIX = "/.d/"
LIGHTDB_STREAM_PREFIX = "/.s/"
DFU_DESIRED_PREFIX = "/.u/desired"
DFU_ARTIFACT_DOWNLOAD_PREFIX = "/.u/c/"


def join_path(prefix, path):
    if path.startswith("/"):
        path = path[1:]

    if (len(path) == 0):
        return prefix + "#"

    return prefix + path


def set_socket(socket, interface):
    MQTT.set_socket(socket, interface)


class Client:
    def __init__(self, psk_id, psk, socket_pool=None, ssl_context=None):
        # Set up a MiniMQTT Client
        self.mqtt_client = MQTT.MQTT(
            broker=GOLIOTH_MQTT_HOST,
            port=GOLIOTH_MQTT_PORT,
            username=psk_id,
            password=psk,
            client_id=psk_id,
            use_binary_mode=True,
            socket_pool=socket_pool,
            ssl_context=ssl_context,
        )

        # callbacks
        self._on_hello = None
        self._on_echo = None
        self._on_connect = None
        self._on_disconnect = None
        self._on_lightdb_message = None
        self._on_desired_version_changed = None
        self._on_download_artifact = None

        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
        self.mqtt_client.on_message = self._on_mqtt_message

    def connect(self):
        self.mqtt_client.connect()

    def is_connected(self):
        return self.mqtt_client.is_connected()

    @property
    def on_hello(self):
        """Called when server responds with device name.
        Expected method signature is ``on_hello(client, message)``
        """
        return self._on_hello

    @on_hello.setter
    def on_hello(self, method):
        self._on_hello = method

    @property
    def on_echo(self):
        """Called when server responds to echo requests.
        Expected method signature is ``on_echo(client, message)``
        """
        return self._on_echo

    @on_echo.setter
    def on_echo(self, method):
        self._on_echo = method

    @property
    def on_connect(self):
        """Called when device connects to Golioth.
        Expected method signature is ``on_connect(client)``
        """
        return self._on_connect

    @on_connect.setter
    def on_connect(self, method):
        self._on_connect = method

    @property
    def on_disconnect(self):
        """Called when device disconnects to Golioth.
        Expected method signature is ``on_disconnect(client)``
        """
        return self._on_disconnect

    @on_disconnect.setter
    def on_disconnect(self, method):
        self._on_disconnect = method

    @property
    def on_lightdb_message(self):
        """Called when a new message arrives from LightDB State.
        Expected method signature is ``on_lighdb_message(client, path, message)``
        """
        return self._on_lightdb_message

    @on_lightdb_message.setter
    def on_lightdb_message(self, method):
        self._on_lightdb_message = method

    @property
    def on_desired_version_changed(self):
        """Called when a new version is available.
        Expected method signature is ``on_desired_version_changed(client, pkg, version, digest)``
        """
        return self._on_desired_version_changed

    @on_desired_version_changed.setter
    def on_desired_version_changed(self, method):
        self._on_desired_version_changed = method

    @property
    def on_download_artifact(self):
        """Called when a artifact is fetch and downloaded.
        Expected method signature is ``on_download_artifact(client, pkg, version, payload)``
        """
        return self._on_desired_version_changed

    @on_download_artifact.setter
    def on_download_artifact(self, method):
        self._on_download_artifact = method

    def listen_hello(self):
        self.mqtt_client.subscribe("/hello")
        self.loop()

    def listen_echo(self):
        self.mqtt_client.subscribe("/echo")
        self.loop()

    def send_echo(self, payload):
        self.mqtt_client.publish("/echo", payload)

    def listen_lightdb_state_at_path(self, path):
        self.mqtt_client.subscribe(join_path(LIGHTDB_STATE_PREFIX, path))
        self.loop()

    def set_lightdb_state_at_path(self, path, payload):
        self.mqtt_client.publish(
            join_path(LIGHTDB_STATE_PREFIX, path), payload)

    def delete_lightdb_state_at_path(self, path):
        self.mqtt_client.publish(join_path(LIGHTDB_STATE_PREFIX, path), "")

    def send_lightdb_stream_at_path(self, path, payload):
        self.mqtt_client.publish(
            join_path(LIGHTDB_STREAM_PREFIX, path), payload)

    def listen_desired_version(self):
        self.mqtt_client.subscribe(DFU_DESIRED_PREFIX)
        self.loop()

    def download_artifact(self, package, version):
        path = "/.u/c/" + package + "@" + version
        if path in self.mqtt_client._subscribed_topics:
            self.mqtt_client.unsubscribe(path)

        self.mqtt_client.subscribe(path)
        self.loop()

    def send_raw_log(self, level, value):
        payload = {}
        if isinstance(value, str):
            payload["msg"] = value
        elif isinstance(value, object):
            payload = value
        else:
            payload["msg"] = str(value)

        payload["level"] = level
        self.mqtt_client.publish("/logs", json.dumps(payload))

    def log_info(self, payload):
        self.send_raw_log("INFO", payload)

    def log_warn(self, payload):
        self.send_raw_log("WARN", payload)

    def log_error(self, payload):
        self.send_raw_log("ERROR", payload)

    def log_debug(self, payload):
        self.send_raw_log("DEBUG", payload)

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        # This function will be called when the client is connected
        # successfully to Golioth.
        if self._on_connect is not None:
            self._on_connect(self)

    def _on_mqtt_disconnect(self, client, userdata, rc):
        # This method is called when the client is disconnected
        if self._on_disconnect is not None:
            self._on_disconnect(self)

    def _on_mqtt_message(self, client, topic, message):
        """Method callled when a client's subscribed feed has a new
        value.
        :param str topic: The topic of the feed with a new value.
        :param str message: The new value
        """
        if not topic.startswith("/"):
            topic = "/" + topic

        if topic.startswith("/hello") and self._on_hello is not None:
            self._on_hello(self, str(message, "utf-8"))

        if topic.startswith("/echo") and self._on_echo is not None:
            self._on_echo(self, str(message, "utf-8"))

        if topic.startswith(LIGHTDB_STATE_PREFIX) and self._on_lightdb_message is not None:
            topic = topic.replace(LIGHTDB_STATE_PREFIX, "")
            self._on_lightdb_message(self, topic, str(message, "utf-8"))

        if topic.startswith(DFU_DESIRED_PREFIX) and self._on_desired_version_changed is not None:
            data = json.loads(str(message, "utf-8"))
            if data is not None:
                if "components" in data and data["components"] is not None:
                    for c in data["components"]:
                        self._on_desired_version_changed(
                            self, c["package"], c["version"], c["hash"])

        if topic.startswith("/.u/c") and self._on_download_artifact is not None:
            path = topic.replace("/.u/c/", "")
            at_index = path.index("@")
            pkg = path[0:at_index]
            version = path[at_index+1:]
            self._on_download_artifact(self, pkg, version, message)

    def loop(self):
        self.mqtt_client.loop()
