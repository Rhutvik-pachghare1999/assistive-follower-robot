import sys
import rclpy
import subprocess
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Image
from cv_bridge import CvBridge
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QVBoxLayout,
    QWidget,
    QFrame,
    QPushButton,
    QHBoxLayout,
)


class RobotDataSubscriber(Node):
    def __init__(self, update_gui_callback):
        super().__init__("robot_data_subscriber")
        self.bridge = CvBridge()
        self.update_gui_callback = update_gui_callback

        self.create_subscription(LaserScan, "/rpi_11/scan", self.scan_callback, 10)
        self.create_subscription(Image, "/color/preview/image", self.image_callback, 10)

    def scan_callback(self, msg):
        self.update_gui_callback(f"LaserScan Data:\n{msg.ranges}", None)

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        self.update_gui_callback(None, cv_image)


class RobotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Data Viewer")
        self.setGeometry(100, 100, 800, 600)
        self.rosbag_process = None

        # Layout
        self.main_layout = QHBoxLayout()
        self.button_layout = QVBoxLayout()
        self.display_layout = QVBoxLayout()

        # Buttons
        self.lidar_button = QPushButton("Lidar Data")
        self.camera_button = QPushButton("Camera Data")
        self.record_button = QPushButton("Start Recording")
        self.stop_record_button = QPushButton("Stop Recording")
        self.lidar_button.clicked.connect(self.show_lidar_data)
        self.camera_button.clicked.connect(self.show_camera_data)
        self.record_button.clicked.connect(self.start_rosbag_recording)
        self.stop_record_button.clicked.connect(self.stop_rosbag_recording)

        self.button_layout.addWidget(self.record_button)
        self.button_layout.addWidget(self.stop_record_button)
        self.button_layout.addWidget(self.lidar_button)
        self.button_layout.addWidget(self.camera_button)

        # Partition Frame
        self.partition = QFrame()
        self.partition.setFrameShape(QFrame.VLine)
        self.partition.setFrameShadow(QFrame.Sunken)

        # Lidar Data Frame
        self.lidar_frame = QFrame()
        self.lidar_frame.setFrameShape(QFrame.Box)
        self.lidar_frame.setFixedSize(600, 250)
        self.lidar_label = QLabel(self.lidar_frame)
        self.lidar_label.setAlignment(Qt.AlignCenter)
        self.lidar_label.setGeometry(10, 10, 580, 230)
        self.lidar_frame.setVisible(False)

        # Camera Data Frame
        self.camera_frame = QFrame()
        self.camera_frame.setFrameShape(QFrame.Box)
        self.camera_frame.setFixedSize(600, 250)
        self.camera_label = QLabel(self.camera_frame)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setGeometry(10, 10, 580, 230)
        self.camera_frame.setVisible(False)

        # Status Label
        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.display_layout.addWidget(self.status_label)
        self.display_layout.addWidget(self.lidar_frame, alignment=Qt.AlignCenter)
        self.display_layout.addWidget(self.camera_frame, alignment=Qt.AlignCenter)

        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addWidget(self.partition)
        self.main_layout.addLayout(self.display_layout)
        self.setLayout(self.main_layout)

        # ROS2 Node
        self.node = RobotDataSubscriber(self.update_gui)
        self.timer = QTimer()
        self.timer.timeout.connect(self.spin_ros)
        self.timer.start(100)

    def show_lidar_data(self):
        self.lidar_frame.setVisible(True)
        self.camera_frame.setVisible(False)
        self.status_label.setText("Status: Displaying Lidar Data")

    def show_camera_data(self):
        self.camera_frame.setVisible(True)
        self.lidar_frame.setVisible(False)
        self.status_label.setText("Status: Displaying Camera Data")

    def start_rosbag_recording(self):
        if self.rosbag_process is None:
            self.rosbag_process = subprocess.Popen(
                ["ros2", "bag", "record", "-a", "--output", "rosbag_recording"]
            )
            self.status_label.setText("Status: Recording Started")

    def stop_rosbag_recording(self):
        if self.rosbag_process is not None:
            self.rosbag_process.terminate()
            self.rosbag_process = None
            self.status_label.setText("Status: Recording Stopped")

    def update_gui(self, lidar_text, camera_image):
        if lidar_text is not None:
            self.lidar_label.setText(lidar_text)
        if camera_image is not None:
            q_img = QImage(
                camera_image.data,
                camera_image.shape[1],
                camera_image.shape[0],
                camera_image.shape[1] * 3,
                QImage.Format_RGB888,
            )
            self.camera_label.setPixmap(QPixmap.fromImage(q_img))

    def spin_ros(self):
        rclpy.spin_once(self.node, timeout_sec=0.01)


def main():
    rclpy.init()
    app = QApplication(sys.argv)
    gui = RobotGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
