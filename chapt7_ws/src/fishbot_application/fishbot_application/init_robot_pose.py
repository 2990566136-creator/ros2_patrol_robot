"""初始化ROS 2 导航栈中的机器人初始位姿"""
from geometry_msgs.msg import PoseStamped           # 构建包含时间戳和坐标系信息的位姿消息
from nav2_simple_commander.robot_navigator import BasicNavigator    # 提供简化导航操作的高级接口
import rclpy

# 设置机器人的初始位置坐标，并通知导航系统
def main():
    rclpy.init()
    navigator = BasicNavigator()

    initial_pose = PoseStamped()
    initial_pose.header.frame_id = 'map'
    initial_pose.header.stamp = navigator.get_clock().now().to_msg()    # 获取当前时间戳给header.stamp
    initial_pose.pose.position.x = 0.0
    initial_pose.pose.position.y = 0.0
    initial_pose.pose.orientation.w = 1.0
    
    navigator.setInitialPose(initial_pose)      # 将配置好的位姿发送给导航系统
    navigator.waitUntilNav2Active()         # 等待导航变为可用状态
    # rclpy.spin(navigator)
    rclpy.shutdown()

    if __name__ == '__main__':
        main()
