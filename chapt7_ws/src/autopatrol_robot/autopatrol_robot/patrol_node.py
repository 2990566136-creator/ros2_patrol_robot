import rclpy
from geometry_msgs.msg import PoseStamped, Pose
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from tf2_ros import TransformListener, Buffer
from tf_transformations import euler_from_quaternion, quaternion_from_euler
from rclpy.duration import Duration
from autopatrol_interfaces.srv import SpeechText
from sensor_msgs.msg import Image   # 导入Image消息类型，用于接收图像数据
from cv_bridge import CvBridge      # 导入CvBridge类，用于在ROS图像消息和OpenCV图像之间进行转换
import cv2                  # 导入OpenCV库，用于图像处理和保存


class PatrolNode(BasicNavigator):
    def __init__(self, node_name='patrol_node'):
        super().__init__(node_name)
        # 导航相关定义
        self.declare_parameter('initial_point', [0.0, 0.0, 0.0])  
        self.declare_parameter('target_point', [0.0, 0.0, 0.0, 1.0, 1.0, 1.57])
        self.initial_point = self.get_parameter('initial_point').value 
        self.target_point = self.get_parameter('target_point').value
        self.buffer_ = Buffer()   # 创建Buffer对象，用于存储坐标变换数据。使用方式：后续通过 TransformListener 填充此缓冲区
        self.listener_ = TransformListener(self.buffer_, self)  # 创建TransformListener对象，并传入Buffer对象，订阅/tf和/tf_static话题，然后填充Buffer对象
        # 语音合成客户端
        self.speech_client_ = self.create_client(SpeechText, 'speech_text')
        # 订阅与保存图像相关定义
        self.declare_parameter('image_save_path', '')
        self.image_save_path = self.get_parameter('image_save_path').value
        self.bridge = CvBridge()
        self.latest_image = None
        self.subscriptions_image = self.create_subscription(
            Image, '/camera_sensor/image_raw', self.image_callback, 10)

    def get_pose_by_xyyaw(self, x, y, yaw):
        """
        通过x，y，yaw合成PoseStamped消息
        """
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.pose.position.x = x
        pose.pose.position.y = y
        rotation_quaternion = quaternion_from_euler(0, 0, yaw)
        pose.pose.orientation.x = rotation_quaternion[0]
        pose.pose.orientation.y = rotation_quaternion[1]
        pose.pose.orientation.z = rotation_quaternion[2]
        pose.pose.orientation.w = rotation_quaternion[3]
        return pose

    def init_robot_pose(self):
        """
        初始化机器人位姿
        """
        # 从参数获取初始位姿信息
        self.initial_pose = self.get_parameter('initial_point').value
        # 合成位姿并进行初始化
        self.setInitialPose(self.get_pose_by_xyyaw(
            self.initial_pose[0], self.initial_pose[1], self.initial_pose[2]))
        # 等待导航系统启动
        self.waitUntilNav2Active()
    
    def get_target_points(self):
        """
        通过参数值获取目标点集合
        """
        points = []
        self.target_points_ = self.get_parameter('target_point').value
        for index in range(int(len(self.target_points_) / 3)):
            x = self.target_points_[index * 3]
            y = self.target_points_[index * 3 + 1]
            yaw = self.target_points_[index * 3 + 2]
            points.append([x, y, yaw])
            self.get_logger().info(f'获取到目标点：{index} -> (x={x}, y={y}, yaw={yaw})')
        return points

    def nav_to_pose(self, target_pose):
        """
        导航到目标点
        """
        self.waitUntilNav2Active()
        result = self.goToPose(target_pose)
        while not self.isTaskComplete():
            feedback = self.getFeedback()
            if feedback:
                self.get_logger().info(
                    f'剩余距离：{feedback.distance_remaining} , 预计：{Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9}秒后到达')
        
        # 最终结果判断
        result = self.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info('导航成功')
        elif result == TaskResult.CANCELED:
            self.get_logger().warn('导航被取消')
        elif result == TaskResult.FAILED:
            self.get_logger().error('导航失败')
        else:
            self.get_logger().error('返回状态失效')

    def get_current_pose(self):
        """
        通过TF获取当前位姿
        """
        while rclpy.ok():
            try:
                """
                    使用 lookup_transform 查询从 'map' 到 'base_footprint' 的坐标变换。
                    参数说明：
                    'map'：目标坐标系。
                    'base_footprint'：源坐标系。
                    rclpy.time.Time(seconds=0)：查询最新可用的时间戳。seconds=0表示使用当前时间戳。（即当前时刻）
                    rclpy.time.Duration(seconds=1)：等待变换的最大时间。seconds=1表示等待1秒。1秒内没有获取到所需的坐标变换时，会抛出异常。
                    使用方式：当变换不可用时会抛出异常，因此需要用 try-except 处理。
                """
                tf = self.buffer_.lookup_transform('map', 'base_footprint', 
                    rclpy.time.Time(seconds=0), rclpy.time.Duration(seconds=1))
                transform = tf.transform    # 提取变换结果中的变换数据
                # 将四元数数转换成欧拉角
                rotation_euler = euler_from_quaternion([
                    transform.rotation.x,
                    transform.rotation.y,
                    transform.rotation.z,
                    transform.rotation.w
                ])
                self.get_logger().info(f'平移：{transform.translation},旋转四元数:{transform.rotation}, 旋转欧拉角：{rotation_euler}')
                return transform
            # 捕获异常并打印警告信息。
            except Exception as e:
                self.get_logger().warn(f'不能够获取坐标变换，原因：{str(e)}')

    def speech_text(self, text):
        """
        调用服务播放语音
        """
        while not self.speech_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('等待服务启动...')
        
        request = SpeechText.Request()
        request.text = text
        # 异步调用服务，并等待结果
        future = self.speech_client_.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        if future.result() is not None:
            result = future.result().result
            if result:
                self.get_logger().info(f'播放成功：{text}')
            else:
                self.get_logger().warn(f'播放失败：{text}')
        else:
            self.get_logger().warn('服务调用失败')

    def image_callback(self, msg):
        """
        将最新的消息放到latest_image中
        """
        self.latest_image = msg

    def record_image(self):
        """
        记录图像
        """
        if self.latest_image is not None:
            pose = self.get_current_pose()          # 获取当前位姿信息，包含平移和旋转信息
            cv_image = self.bridge.imgmsg_to_cv2(self.latest_image)         # 将 ROS 图像消息转换为 OpenCV 格式
            # 将图像保存到指定路径
            cv2.imwrite(
                f'{self.image_save_path}image_{pose.translation.x:3.2f}_{pose.translation.y:3.2f}.png', cv_image)


def main():
    rclpy.init()
    patrol = PatrolNode()
    patrol.speech_text(text='正在初始化位置')
    patrol.init_robot_pose()
    patrol.speech_text(text='初始化位置完成')

    while rclpy.ok(): 
        points = patrol.get_target_points()
        for point in points:
            x, y, yaw = point[0], point[1], point[2]
            # 导航到服务点
            target_pose = patrol.get_pose_by_xyyaw(x, y, yaw)
            # 记录图像
            patrol.speech_text(text=f'正在导航到目标点：x={x}, y={y}')
            patrol.nav_to_pose(target_pose)
            patrol.speech_text(text=f'已到达目标点：x={x}, y={y}，正在记录图像')
            patrol.record_image()
            patrol.speech_text(text=f'图像记录完成')
    rclpy.shutdown()
