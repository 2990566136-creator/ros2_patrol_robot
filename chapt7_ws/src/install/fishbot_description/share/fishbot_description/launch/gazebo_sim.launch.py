"""用于启动多个节点"""
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory # 获取share的路径
import os


def generate_launch_description():
    """产生launch描述，名字不能变"""
    # 获取默认路径
    urdf_package_path = get_package_share_directory('fishbot_description')
    default_xacro_path = os.path.join(urdf_package_path, 'urdf', 'fishbot/fishbot.urdf.xacro')    # /* 获取urdf文件路径 */
    # default_rviz_config_path = os.path.join(urdf_package_path, 'config', 'display_robot_model.rviz')    # 直接使用保存配置好的rviz文件
    default_gazebo_world_path = os.path.join(urdf_package_path, 'world', 'custom_room_one.world')

    # 为launch声明参数,声明一个urdf目录的参数，方便修改
    """
    在 ROS 2 的 launch 文件中声明一个可配置的参数 model，用于指定机器人模型文件（通常是 URDF 文件）的路径
    1、launch.actions.DeclareLaunchArgument：
    这是 ROS 2 中用于声明 launch 参数的类,它允许用户在启动 launch 文件时传入自定义参数，或者使用默认值
    2、name = 'model'，指定参数的名称为 'model'，用户可以通过这个名称在启动时传入自定义的 URDF 文件路径
    3、default_value = str(default_model_path)，指定参数的默认值为默认的 URDF 文件路径
    4、description = '加载模型文件路径'，指定参数的描述信息，用于在 launch 文件中显示
    """
    action_declare_arg_mode_path = launch.actions.DeclareLaunchArgument(
        name = 'model', default_value = str(default_xacro_path),
        description = '加载模型文件路径')
    
    # 通过文件路径，获取内容，并转换成参数值对象，以供传入ros_state_publisher节点使用
    """
    从指定的 URDF 文件中读取机器人模型的描述内容，并将其作为参数传递给 ROS 2 节点
    1、launch.substitutions.LaunchConfiguration('model')：
    这是一个 Launch 配置参数，表示从 launch 文件中获取名为 'model' 的参数值。这个参数通常用于指定 URDF 文件的路径
    2、launch.substitutions.Command(['cat', ...])：
    使用 Command 来执行 shell 命令。这里的命令是 cat，它会读取 'model' 参数指定的文件内容（即 URDF 文件的内容）
    3、launch_ros.parameter_descriptions.ParameterValue(...)：
    将上述命令的输出（URDF 文件内容）封装为一个参数值对象，并指定其类型为字符串（value_type=str）。这个对象后续会被用作 ROS 2 节点的参数
    """
    robot_description = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.Command(
            ['xacro ', launch.substitutions.LaunchConfiguration('model')]),
            value_type=str
        )
    
    # 状态发布节点
    robot_state_publisher_node = launch_ros.actions.Node(
        package = 'robot_state_publisher',
        executable = 'robot_state_publisher',
        parameters = [{'robot_description': robot_description}]
    )

    # 通过IncludeLaunchDescription包含另外一个launch文件，书本4-65
    action_launch_gazebo = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            [get_package_share_directory('gazebo_ros'), '/launch', '/gazebo.launch.py']
            ),
            # 传递参数
            launch_arguments = [('world', default_gazebo_world_path), ('verbose', 'true')]
    )

    # 请求gazebo加载机器人
    spawn_entity_node = launch_ros.actions.Node(
        package = 'gazebo_ros',
        executable = 'spawn_entity.py',
        arguments = ['-topic', '/robot_description', '-entity', 'fishbot'],
    )

    # 加载并激活 fishbot_joint_state_broadcaster控制器
    load_joint_state_broadcaster = launch.actions.ExecuteProcess(
        cmd = ['ros2', 'control', 'load_controller', '--set-state', 'active', 'fishbot_joint_state_broadcaster'],
        output = 'screen'
    )

    # 加载并激活 fishbot_effort_controller控制器
    load_fishbot_effort_controller = launch.actions.ExecuteProcess(
        cmd = ['ros2', 'control', 'load_controller', '--set-state', 'active', 'fishbot_effort_controller'],
        output = 'screen'
    )

    # 加载并激活 fishbot_diff_drive_controller控制器
    load_fishbot_diff_drive_controller = launch.actions.ExecuteProcess(
        cmd = ['ros2', 'control', 'load_controller', '--set-state', 'active', 'fishbot_diff_drive_controller'],
        output = 'screen'
    )



    # 合成启动描述并返回
    lanch_description = launch.LaunchDescription([
        action_declare_arg_mode_path,
        robot_state_publisher_node,
        action_launch_gazebo,
        spawn_entity_node,
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action = spawn_entity_node,
                on_exit = [load_joint_state_broadcaster]
            )
        ),
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action = load_joint_state_broadcaster,
                on_exit = [load_fishbot_diff_drive_controller]
            )
        ),
    ])

    return lanch_description