Fork of <https://github.com/adafruit/Adafruit_CircuitPython_MiniMQTT>.

The only change was on `this line <https://github.com/adafruit/Adafruit_CircuitPython_MiniMQTT/blob/main/adafruit_minimqtt/adafruit_minimqtt.py#L843>` that tries to convert the MQTT payload to a string, but in our use case ( specially for OTA) we want to handle the raw binary.