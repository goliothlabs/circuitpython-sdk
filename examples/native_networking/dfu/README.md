# Golioth DFU Sample with CircuitPython

This samples uses Golioth's DFU feature. Users can create artifacts/releases, and with this sample, the device is going to download the latest artifacts and save on flash in the `/artifacts` folder.

For this sample, you need to change `boot.py` file to put the storage into Read/Write mode.

Tested on ESP32S2.
