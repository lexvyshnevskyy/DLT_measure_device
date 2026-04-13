# measure_device

ROS 2 publisher node for the E7-20 measurement device over RS232.

## Parameters
- `endpoint` (string, default: `measure_device`)
- `publish_rate` (float, default: `10.0`)
- `port` (string, default: `/dev/ttyUSB0`)
- `speed` (int, default: `9600`)
- `frame_id_ready` (string, default: `e720_ready`)
- `frame_id_offline` (string, default: `e720_offline`)
