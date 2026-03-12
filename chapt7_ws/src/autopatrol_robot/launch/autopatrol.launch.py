"""用于启动多个节点和参数文件"""
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory # 获取share的路径
import os
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # 获取功能包路与拼接默认路径
    autopatrol_robot_dir = get_package_share_directory('autopatrol_robot')
    patrol_config_path = os.path.join(autopatrol_robot_dir, 'config', 'patrol_config.yaml')
    
    action_node_turtle_control = launch_ros.actions.Node(
        package='autopatrol_robot',
        executable='patrol_node',
        output='screen',
        parameters=[patrol_config_path]
    )

    action_node_patrol_client = launch_ros.actions.Node(
        package='autopatrol_robot',
        executable='speaker',
        output='screen'
    )
    
    # 合成启动描述并返回
    launch_description = launch.LaunchDescription([
        action_node_turtle_control,
        action_node_patrol_client
    ])

    return launch_description
