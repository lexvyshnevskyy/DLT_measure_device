from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    endpoint_arg = DeclareLaunchArgument('endpoint', default_value='measure_device')
    publish_rate_arg = DeclareLaunchArgument('publish_rate', default_value='10.0')
    port_arg = DeclareLaunchArgument('port', default_value='/dev/ttyUSB0')
    speed_arg = DeclareLaunchArgument('speed', default_value='9600')
    frame_id_ready_arg = DeclareLaunchArgument('frame_id_ready', default_value='e720_ready')
    frame_id_offline_arg = DeclareLaunchArgument('frame_id_offline', default_value='e720_offline')

    node = Node(
        package='measure_device',
        executable='measure_device_node',
        name='measure_device_publisher',
        output='screen',
        respawn=True,
        respawn_delay=2.0,
        parameters=[{
            'endpoint': LaunchConfiguration('endpoint'),
            'publish_rate': LaunchConfiguration('publish_rate'),
            'port': LaunchConfiguration('port'),
            'speed': LaunchConfiguration('speed'),
            'frame_id_ready': LaunchConfiguration('frame_id_ready'),
            'frame_id_offline': LaunchConfiguration('frame_id_offline'),
        }],
    )

    return LaunchDescription([
        endpoint_arg,
        publish_rate_arg,
        port_arg,
        speed_arg,
        frame_id_ready_arg,
        frame_id_offline_arg,
        node,
    ])
