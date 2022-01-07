# Golioth DFU + TFT Display Sample with CircuitPython

This samples uses Golioth's DFU feature to download images/bitmaps and show on a TFT Display. The device is going to download the latest artifacts and save on flash in the `/ artifacts` folder. When uploading artifacts to be used with this sample, use the `package` name "emoji".

For this sample, you need to change `boot.py` file to put the storage into Read/Write mode.

### BOM

- Raspberry Pi Pico
- ESP32 with AT Firmware
- 160x128 TFT Display ST7735R
