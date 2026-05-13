from __future__ import annotations

import time
from typing import Any, Dict, Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String
from msgs.msg import E720

from .e720.driver import ParseData
from .rs232.rsconnector import RSConnector


class MeasureDevicePublisher(Node):
    def __init__(self) -> None:
        super().__init__('measure_device')

        self.declare_parameter('publish_rate', 10.0)
        self.declare_parameter('endpoint', 'measure_device')
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('speed', 9600)
        self.declare_parameter('frame_id_ready', 'e720_ready')
        self.declare_parameter('frame_id_offline', 'e720_offline')
        self.declare_parameter('offline_timeout_sec', 1.0)
        self.declare_parameter('offline_publish_period_sec', 1.0)

        self.publish_rate = float(self.get_parameter('publish_rate').value)
        self.endpoint = str(self.get_parameter('endpoint').value)
        self.port = str(self.get_parameter('port').value)
        self.speed = int(self.get_parameter('speed').value)
        self.frame_id_ready = str(self.get_parameter('frame_id_ready').value)
        self.frame_id_offline = str(self.get_parameter('frame_id_offline').value)
        self.offline_timeout_sec = float(self.get_parameter('offline_timeout_sec').value)
        self.offline_publish_period_sec = float(self.get_parameter('offline_publish_period_sec').value)

        self.publisher_ = self.create_publisher(E720, self.endpoint, 10)
        self.parser = ParseData()
        self.connector = RSConnector(port=self.port, speed=self.speed)

        self._last_valid_frame_monotonic: Optional[float] = None
        self._last_offline_publish_monotonic: float = 0.0

        period = 1.0 / self.publish_rate if self.publish_rate > 0.0 else 0.1
        self.timer = self.create_timer(period, self._on_timer)

        self.get_logger().info(
            f'Started measure_device publisher: topic={self.endpoint}, rate={self.publish_rate} Hz, '
            f'port={self.port}, speed={self.speed}, offline_timeout_sec={self.offline_timeout_sec}'
        )

    def _should_publish_offline(self) -> bool:
        now = time.monotonic()

        if self._last_valid_frame_monotonic is not None:
            if now - self._last_valid_frame_monotonic < self.offline_timeout_sec:
                return False

        if now - self._last_offline_publish_monotonic < self.offline_publish_period_sec:
            return False

        self._last_offline_publish_monotonic = now
        return True

    def _on_timer(self) -> None:
        try:
            if not self.connector.is_open():
                if self.connector.reconnect():
                    self.get_logger().info(f'Reconnected serial device on {self.port}')
                else:
                    if self._should_publish_offline():
                        self.publisher_.publish(self._parse_response(None))
                    return

            raw_message = self.connector.read_complete_frame(expected_length=ParseData.FRAME_LENGTH)
            if raw_message is None:
                # No complete frame on this timer tick is normal. Do not report offline
                # until no valid frame has been seen for offline_timeout_sec.
                if self._should_publish_offline():
                    self.publisher_.publish(self._parse_response(None))
                return

            self.parser.parse_data(raw_message)
            data = self.parser.dataReady()
            if data is None:
                if self._should_publish_offline():
                    self.publisher_.publish(self._parse_response(None))
                return

            self._last_valid_frame_monotonic = time.monotonic()
            msg = self._parse_response(data)
            self.publisher_.publish(msg)
        except Exception as exc:
            self.get_logger().error(f'Error in measure_device polling/publish cycle: {exc}')
            if self._should_publish_offline():
                self.publisher_.publish(self._parse_response(None))

    def _parse_response(self, data: Optional[Dict[str, Any]]) -> E720:
        msg = E720()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id_ready if data else self.frame_id_offline

        payload = data or {}
        msg.offset = Float32(data=float(payload.get('OffSet', 0.0) or 0.0))
        msg.level = Float32(data=float(payload.get('Level', 0.0) or 0.0))
        msg.freq = Float32(data=float(payload.get('Freq', 0.0) or 0.0))
        msg.freq10 = Float32(data=float(payload.get('Freq10', 0.0) or 0.0))
        msg.frequency = Float32(data=float(payload.get('Frequency', 0.0) or 0.0))
        msg.limit = String(data=str(payload.get('Limit', '')))
        msg.imparam = String(data=str(payload.get('ImParam', '')))
        msg.secparam = String(data=str(payload.get('SecParam', '')))
        msg.secvalue = Float32(data=float(payload.get('SecValue', 0.0) or 0.0))
        msg.secvalue10 = Float32(data=float(payload.get('SecValue10', 0.0) or 0.0))
        msg.secondvalue = Float32(data=float(payload.get('SecondValue', 0.0) or 0.0))
        msg.imvalue = Float32(data=float(payload.get('ImValue', 0.0) or 0.0))
        msg.imvalue10 = Float32(data=float(payload.get('ImValue10', 0.0) or 0.0))
        msg.firstvalue = Float32(data=float(payload.get('FirstValue', 0.0) or 0.0))
        msg.onchange = Float32(data=float(payload.get('OnChange', 0.0) or 0.0))
        msg.timestamp = Float32(data=float(payload.get('TimeStamp', 0.0) or 0.0))
        return msg


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MeasureDevicePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
