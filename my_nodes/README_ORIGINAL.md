
# Reactive Gap Follower & Vision-Based Angle Predictor (ROS 2)

This ROS 2 package combines **reactive obstacle avoidance** using LIDAR with a **deep learning-based angle prediction system** using camera input. The system is designed for real-time navigation and directional control of a mobile robot.

---

## 📦 Package Overview

This package includes:

- `gap_finder.py`: Implements the Follow Gap algorithm for obstacle avoidance.
- `predict_publisher_node.py`: Uses a pretrained neural network to estimate the object's relative position and angle from the camera feed.
- `shoe_model.pth`: A trained PyTorch ResNet18 model for image-to-angle prediction (placed under `models/` directory).

---

## 📁 Folder Structure

```
my_nodes/
├── scripts/
│   ├── gap_finder.py
│   └── predict_publisher_node.py
├── models/
│   └── shoe_model.pth
├── package.xml
├── setup.py
└── README.md
```

---

## ## Dependencies

Ensure the following packages are installed in your environment:

### ROS 2 Dependencies:
- `rclpy`
- `sensor_msgs`
- `geometry_msgs`
- `nav_msgs`
- `std_msgs`
- `cv_bridge`
- `ament_index_python`

### Python Libraries:
```bash
pip install torch torchvision opencv-python numpy
```

---

## ## Node Descriptions

### `gap_finder.py`

- **Subscribes to:**
  - `/rpi_11/scan` (LaserScan)
  - `/rpi_11/prediction_topic` (nav_msgs/Path for heading)
- **Publishes to:**
  - `/rpi_11/cmd_vel` (geometry_msgs/Twist)
- **Description:**
  - Performs real-time obstacle avoidance using LIDAR.
  - Smooths LIDAR data and finds the widest navigable gap.
  - Masks a “bubble” around the closest obstacle to avoid collisions.
  - Aligns movement toward a predicted heading angle received from the vision model.

---

### `predict_publisher_node.py`

- **Subscribes to:**
  - `/color/preview/image` (sensor_msgs/Image)
- **Publishes to:**
  - `/rpi_11/prediction_topic` (std_msgs/String with heading info)
- **Description:**
  - Loads a pretrained ResNet18 model for inference.
  - Predicts the object's X offset, Z distance, and computes angle from camera input.
  - Publishes the computed angle as a formatted string.

---

## ## Model Format

The model must output the following values:
```
[x_offset_norm, z_distance_norm, sin(theta), cos(theta)]
```

Place your `.pth` file at:
```
my_nodes/models/shoe_model.pth
```

Update the path in `predict_publisher_node.py` if needed:
```python
share_dir = get_package_share_directory('my_nodes')
model_path = os.path.join(share_dir, 'shoe_model.pth')
```

---

## ## Running the Nodes

### 1. Build the workspace
```bash
cd ~/ros2_ws
colcon build
source install/setup.bash
```

### 2. Run the prediction node
```bash
ros2 run my_nodes predict_publisher_node.py
```

### 3. Run the gap follower node
```bash
ros2 run my_nodes gap_finder.py
```

> Make sure your camera and LIDAR are publishing data to `/color/preview/image` and `/rpi_11/scan` respectively.

---

## ## Parameters to Tune

| Parameter         | Location         | Default | Description                              |
|------------------|------------------|---------|------------------------------------------|
| `WINDOW_SIZE`     | gap_finder.py     | 10      | Smoothing window size                    |
| `RANGE_THRESHOLD` | gap_finder.py     | 1.0     | Minimum distance to consider free space  |
| `BUBBLE_RADIUS`   | gap_finder.py     | 10      | Radius around closest object to mask     |
| `VELOCITY_LIMITS` | gap_finder.py     | See code | Angular limits to reduce speed safely    |

---

## ## Input Topics

| Topic                     | Type               | Description                       |
|--------------------------|--------------------|-----------------------------------|
| `/rpi_11/scan`           | sensor_msgs/LaserScan | LIDAR data for navigation         |
| `/color/preview/image`   | sensor_msgs/Image  | RGB camera feed for vision model |
| `/rpi_11/prediction_topic` | nav_msgs/Path OR std_msgs/String | Predicted heading or debug text |

---


