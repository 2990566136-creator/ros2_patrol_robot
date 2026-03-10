"""用于启动多个节点"""
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory # 获取share的路径
import os

# ROS2 Navigation2的启动文件，包含了导航所需的所有节点和配置，主要用于启动机器人导航系统

def generate_launch_description():
    """产生launch描述，名字不能变"""
    # 获取功能包路与拼接默认路径
    fishbot_navigation2_dir = get_package_share_directory('fishbot_navigation2')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    rviz2_config_dir = os.path.join(nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz') # 构建 RViz2 配置文件路径
    
    # 创建launch配置参数
    # 创建可配置的启动参数 - 仿真时间开关
    use_sim_time = launch.substitutions.LaunchConfiguration(
        'use_sim_time', default='true')
    # 创建可配置的启动参数 - 地图文件路径
    map_yaml_path = launch.substitutions.LaunchConfiguration(
        'map', default=os.path.join(fishbot_navigation2_dir, 'maps', 'room2.yaml'))
    # 创建可配置的启动参数 - 导航参数文件路径
    nav2_param_path = launch.substitutions.LaunchConfiguration(
        'params_file', default=os.path.join(fishbot_navigation2_dir, 'config', 'nav2_params.yaml'))
    
    # 声明launch参数
    """
    在 ROS 2 的 launch 文件中声明可配置参数：
    1、use_sim_time - 是否使用仿真时间
    2、map - 地图文件路径
    3、params_file - 导航参数文件路径
    """
    # 声明 use_sim_time 参数，允许用户在启动时覆盖
    action_declare_arg_mode1_path = launch.actions.DeclareLaunchArgument(
        name = 'use_sim_time', default_value = use_sim_time,
        description = 'Use simulation (Gazebo) clock if true')
    # 声明 map 参数，指定地图文件路径
    action_declare_arg_mode2_path = launch.actions.DeclareLaunchArgument(
        name = 'map', default_value = map_yaml_path,
        description = 'Full path to map file to load')
    # 声明 params_file 参数，指定导航配置文件路径
    action_declare_arg_mode3_path = launch.actions.DeclareLaunchArgument(
        name = 'params_file', default_value = nav2_param_path,
        description = 'Full path to param file to load')

    # 通过IncludeLaunchDescription包含另外一个launch文件，书本4-65
    # 包含 nav2_bringup 启动文件

    # ==================== 包含 Nav2 启动文件 ====================
    # 通过 IncludeLaunchDescription 包含 nav2_bringup 的启动文件
    # 这是 Navigation 2 的核心启动文件，会启动所有导航相关节点
    action_launch_bringup_launch = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
            # 传递启动参数给被包含的 launch 文件
            launch_arguments = {
                'map' : map_yaml_path,
                'use_sim_time' : use_sim_time,
                'params_file' : nav2_param_path}.items(),
        )

    # 启动rviz2可视化工具，创建节点
    action_rviz2_node = launch_ros.actions.Node(
        package = 'rviz2',
        executable = 'rviz2',
        name = 'rviz2',
        arguments = ['-d', rviz2_config_dir],  # 加载 RViz 配置文件
        parameters = [{'use_sim_time': use_sim_time}],  # 设置仿真时间参数
        output = 'screen'
    )

    # 合成启动描述并返回
    launch_description = launch.LaunchDescription([
        action_declare_arg_mode1_path,
        action_declare_arg_mode2_path,
        action_declare_arg_mode3_path,
        action_launch_bringup_launch,
        action_rviz2_node
    ])

    return launch_description