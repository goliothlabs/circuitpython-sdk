# Golioth Logs Sample with CircuitPython

This samples uses Golioth's Device Logs feature. When the device is connected to the platform, it will send some logs with the device information. Tested on ESP32S2.

Example:

```
$ goliothctl logs
[2022-01-07T15:02:50Z] level:DEBUG  module:"default"  message:"Hello 1"  device_id:"61ae0d2495fd466888055c92" metadata:"{}"
[2022-01-07T15:02:42Z] level:INFO  module:"native_networking"  message:"connected"  device_id:"61ae0d2495fd466888055c92" metadata:"{"hostname":"espressif"}"
[2022-01-07T15:02:38Z] level:DEBUG  module:"default"  message:"device connected from CircuitPython"  device_id:"61ae0d2495fd466888055c92" metadata:"{}"
```
