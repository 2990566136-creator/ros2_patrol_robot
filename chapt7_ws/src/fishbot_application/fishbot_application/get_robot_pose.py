import rclpy
from rclpy.node import Node
"""
Buffer：用于缓存和查询坐标变换数据。（存储TF数据帧）
TransformListener：监听并填充 Buffer 中的变换数据（订阅TF数据）
使用方式：结合使用这两个类来实现坐标变换的监听与查询。
"""
from tf2_ros import TransformListener, Buffer       
from tf_transformations import euler_from_quaternion    # 四元数转换欧拉角


class TFListener(Node):
    def __init__(self):
        super().__init__('tf2_listener')
        self.tf_buffer = Buffer()   # 创建Buffer对象，用于存储坐标变换数据。使用方式：后续通过 TransformListener 填充此缓冲区
        self.tf_listener = TransformListener(self.tf_buffer, self)  # 创建TransformListener对象，并传入Buffer对象，订阅/tf和/tf_static话题，然后填充Buffer对象
        self.timer = self.create_timer(1, self.get_transform)   # 1秒调用1次get_transform()方法查询TF变换

    def get_transform(self):
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
            result = self.tf_buffer.lookup_transform('map', 'base_footprint', 
                rclpy.time.Time(seconds=0), rclpy.time.Duration(seconds=1))
            transform = result.transform    # 提取变换结果中的变换数据
            # 将四元数数转换成欧拉角
            rotation_euler = euler_from_quaternion([
                transform.rotation.x,
                transform.rotation.y,
                transform.rotation.z,
                transform.rotation.w
            ])
            self.get_logger().info(f'平移：{transform.translation},旋转四元数:{transform.rotation}, 旋转欧拉角：{rotation_euler}')
        # 捕获异常并打印警告信息。
        except Exception as e:
            self.get_logger().warn(f'不能够获取坐标变换，原因：{str(e)}')
    

def main():
    rclpy.init()
    node = TFListener()
    rclpy.spin(node)
    rclpy.shutdown()