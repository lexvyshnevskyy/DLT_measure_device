from __future__ import annotations

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

        self.publish_rate = float(self.get_parameter('publish_rate').value)
        self.endpoint = str(self.get_parameter('endpoint').value)
        self.port = str(self.get_parameter('port').value)
        self.speed = int(self.get_parameter('speed').value)
        self.frame_id_ready = str(self.get_parameter('frame_id_ready').value)
        self.frame_id_offline = str(self.get_parameter('frame_id_offline').value)

        self.publisher_ = self.create_publisher(E720, self.endpoint, 10)
        self.parser = ParseData()
        self.connector = RSConnector(port=self.port, speed=self.speed)

        period = 1.0 / self.publish_rate if self.publish_rate > 0.0 else 0.1
        self.timer = self.create_timer(period, self._on_timer)

        self.get_logger().info(
            f'Started measure_device publisher: topic={self.endpoint}, rate={self.publish_rate} Hz, '
            f'port={self.port}, speed={self.speed}'
        )

    def _on_timer(self) -> None:
        try:
            if not self.connector.is_open():
                if self.connector.reconnect():
                    self.get_logger().info(f'Reconnected serial device on {self.port}')
                else:
                    self.publisher_.publish(self._parse_response(None))
                    return

            raw_message = self.connector.read_complete_frame(expected_length=22)
            if raw_message is None:
                self.publisher_.publish(self._parse_response(None))
                return

            self.parser.parse_data(raw_message)
            data = self.parser.dataReady()
            msg = self._parse_response(data)
            self.publisher_.publish(msg)
        except Exception as exc:
            self.get_logger().error(f'Error in measure_device polling/publish cycle: {exc}')
            self.publisher_.publish(self._parse_response(None))

    def _parse_response(self, data: Optional[Dict[str, Any]]) -> E720:
        msg = E720()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id_ready if data else self.frame_id_offline

        payload = data or {}
        msg.OffSet = Float32(data=float(payload.get('OffSet', 0.0) or 0.0))
        msg.Level = Float32(data=float(payload.get('Level', 0.0) or 0.0))
        msg.Freq = Float32(data=float(payload.get('Freq', 0.0) or 0.0))
        msg.Freq10 = Float32(data=float(payload.get('Freq10', 0.0) or 0.0))
        msg.Frequency = Float32(data=float(payload.get('Frequency', 0.0) or 0.0))
        msg.Limit = String(data=str(payload.get('Limit', '')))
        msg.ImParam = String(data=str(payload.get('ImParam', '')))
        msg.SecParam = String(data=str(payload.get('SecParam', '')))
        msg.SecValue = Float32(data=float(payload.get('SecValue', 0.0) or 0.0))
        msg.SecValue10 = Float32(data=float(payload.get('SecValue10', 0.0) or 0.0))
        msg.SecondValue = Float32(data=float(payload.get('SecondValue', 0.0) or 0.0))
        msg.ImValue = Float32(data=float(payload.get('ImValue', 0.0) or 0.0))
        msg.ImValue10 = Float32(data=float(payload.get('ImValue10', 0.0) or 0.0))
        msg.FirstValue = Float32(data=float(payload.get('FirstValue', 0.0) or 0.0))
        msg.OnChange = Float32(data=float(payload.get('OnChange', 0.0) or 0.0))
        msg.TimeStamp = Float32(data=float(payload.get('TimeStamp', 0.0) or 0.0))
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
