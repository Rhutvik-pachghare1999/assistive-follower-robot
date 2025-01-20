import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image

import torch
from torchvision import transforms, models
import torch.nn as nn
import math
import os
from ament_index_python.packages import get_package_share_directory


class CameraPredictorNode(Node):

    def __init__(self):
        super().__init__("camera_predictor_node")

        # ROS setup
        self.subscription = self.create_subscription(
            Image, "/color/preview/image", self.image_callback, 10
        )
        self.publisher_ = self.create_publisher(String, "/rpi_11/prediction_topic", 10)

        # Load model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = models.resnet18(weights=None)
        self.model.fc = nn.Linear(self.model.fc.in_features, 4)

        share_dir = get_package_share_directory("my_nodes")
        model_path = os.path.join(share_dir, "shoe_model.pth")
        state_dict = torch.load(model_path, map_location=self.device)
        cleaned_state_dict = {
            k.replace("backbone.", ""): v for k, v in state_dict.items()
        }
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
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

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

            # Publish
            out_msg = String()
            out_msg.data = (
                f"X Offset: {x_offset:.1f} mm, "
                f"Z Distance: {z_distance:.1f} mm, "
                f"Angle: {angle_deg:.1f} deg"
            )
            self.publisher_.publish(out_msg)
            self.get_logger().info(f"Published: {out_msg.data}")

        except Exception as e:
            self.get_logger().error(f"Failed to process image: {str(e)}")


def main(args=None):
    rclpy.init(args=args)
    node = CameraPredictorNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
