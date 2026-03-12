from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from rclpy.duration import Duration


def main():
    rclpy.init()
    navigator = BasicNavigator()

    # 等待导航启动完成
    navigator.waitUntilNav2Active()

    # 设置目标点坐标
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = 'map'
    goal_pose.header.stamp = navigator.get_clock().now().to_msg()    # 获取当前时间戳给header.stamp
    goal_pose.pose.position.x = 2.0
    goal_pose.pose.position.y = 2.0
    goal_pose.pose.orientation.w = 1.0
    
    # 发送目标接收反馈结果
    navigator.goToPose(goal_pose)
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        navigator.get_logger().info(
            f'剩余距离：{feedback.distance_remaining} , 预计：{Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9}秒后到达')
        # 超时自动取消
        if Duration.from_msg(feedback.navigation_time) > Duration(seconds=600.0):
            navigator.cancelTask()
    
    # 最终结果判断
    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        navigator.get_logger().info('导航成功')
    elif result == TaskResult.CANCELED:
        navigator.get_logger().warn('导航被取消')
    elif result == TaskResult.FAILED:
        navigator.get_logger().error('导航失败')
    else:
        navigator.get_logger().error('返回状态失效')



