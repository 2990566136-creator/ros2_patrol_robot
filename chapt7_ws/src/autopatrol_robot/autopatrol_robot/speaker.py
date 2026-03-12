import rclpy
from rclpy.node import Node
from autopatrol_interfaces.srv import SpeechText    # 导入自定义服务类型
import espeakng


class Speaker(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        # 创建服务端
        self.speech_service_ = self.create_service(SpeechText, 'speech_text', self.speak_text_callback)  # 创建名为'speech_text'的服务，使用SpeechText类型，并指定回调函数speak_text_callback
        self.speaker = espeakng.Speaker()
        self.speaker.voice = 'zh'  # 设置语音为中文
    
    def speak_text_callback(self, request, response):
        self.get_logger().info(f'正在朗读：{request.text}')
        self.speaker.say(request.text)  # 使用espeak-ng库朗读文本
        self.speaker.wait()
        response.result = True  # 设置响应结果为True，表示成功
        return response
    
    
def main():
    rclpy.init()
    node = Speaker('speaker')
    rclpy.spin(node)
    rclpy.shutdown()
