import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path

import torch
import torch.nn as nn
from torchvision import models, transforms
import math
import os
import cv2
from ament_index_python.packages import get_package_share_directory
from cv_bridge import CvBridge


class CameraPredictorNode(Node):

    def __init__(self):
        super().__init__("camera_predictor_node")

        # ROS setup
        self.subscription = self.create_subscription(
            Image, "/color/preview/image", self.image_callback, 10
        )
        self.publisher_ = self.create_publisher(Path, "/rpi_11/prediction_topic", 10)
        self.bridge = CvBridge()

        # Load model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = models.resnet18(weights=None)
        self.model.fc = nn.Linear(self.model.fc.in_features, 4)

        share_dir = get_package_share_directory("my_nodes")
        model_path = os.path.join(share_dir, "models", "shoe_model.pth")
        
        if not os.path.exists(model_path):
            self.get_logger().error(f"Model file not found at {model_path}")
            raise FileNotFoundError(f"Model file not found: {model_path}")

        state_dict = torch.load(model_path, map_location=self.device)

        # Handle both training formats: with or without "backbone." prefix
        cleaned_state_dict = {}
        for k, v in state_dict.items():
            new_key = k.replace("backbone.", "") if k.startswith("backbone.") else k
            cleaned_state_dict[new_key] = v

        self.model.load_state_dict(cleaned_state_dict)
        self.model.to(self.device)
        self.model.eval()

        self.transform = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
        self.get_logger().info("Camera Predictor Node Initialized")

    def image_callback(self, msg):
        try:
            # cv_bridge with "bgr8" returns BGR; convert to RGB for model
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Preprocess
            inp = self.transform(frame).unsqueeze(0).to(self.device)

            # Prediction
            with torch.no_grad():
                pred = self.model(inp).squeeze().cpu().numpy()

            x_norm, z_norm, sin_t, cos_t = pred
            x_offset = x_norm * frame.shape[1]
            z_distance = z_norm * 2000
            angle_rad = math.atan2(sin_t, cos_t)
            angle_deg = math.degrees(angle_rad)

            # Publish as Path message (compatible with gap_finder)
            path_msg = Path()
            path_msg.header.stamp = self.get_clock().now().to_msg()
            path_msg.header.frame_id = "camera_link"

            pose = PoseStamped()
            pose.header = path_msg.header
            pose.pose.position.x = float(x_offset)
            pose.pose.position.y = 0.0
            pose.pose.position.z = float(z_distance / 1000.0)  # Convert to meters

            # Convert angle to quaternion (yaw only)
            pose.pose.orientation.x = 0.0
            pose.pose.orientation.y = 0.0
            pose.pose.orientation.z = math.sin(angle_rad / 2.0)
            pose.pose.orientation.w = math.cos(angle_rad / 2.0)

            path_msg.poses.append(pose)

            self.publisher_.publish(path_msg)
            self.get_logger().info(
                f"Published: x_offset={x_offset:.1f}px, z_dist={z_distance:.1f}mm, angle={angle_deg:.1f}°"
            )

        except Exception as e:
            self.get_logger().error(f"Failed to process image: {str(e)}")


def main(args=None):
    rclpy.init(args=args)
    node = CameraPredictorNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
