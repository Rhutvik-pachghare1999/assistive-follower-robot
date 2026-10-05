#!/usr/bin/env python3

import math
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from nav_msgs.msg import Path

WINDOW_SIZE = 10
RANGE_THRESHOLD = 1.0
BUBBLE_RADIUS = 10
ANGLE_LIMIT = 80
VELOCITY_LIMITS = [(10, 0.5), (20, 0.3), (45, 0.15), (90, 0.05)]


class ReactiveFollowGap(Node):
    def __init__(self):
        super().__init__("FollowGap_node")

        self.lidar_sub = self.create_subscription(
            LaserScan, "/rpi_11/scan", self.lidar_callback, 10
        )
        self.heading_sub = self.create_subscription(
            Path, "/rpi_11/prediction_topic", self.plan_callback, 1
        )
        self.drive_pub = self.create_publisher(Twist, "/rpi_11/cmd_vel", 10)

        self.user_heading_angle = 0.0  # radians

    def plan_callback(self, msg):
        if not msg.poses:
            return
        pose = msg.poses[0]
        q = pose.pose.orientation
        # Convert quaternion to yaw angle
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.user_heading_angle = math.atan2(siny_cosp, cosy_cosp)
        self.get_logger().info(
            f"Received user heading angle: {math.degrees(self.user_heading_angle):.1f}°"
        )

    def preprocess_lidar(self, data):
        ranges = np.array(data.ranges)
        ranges[np.isnan(ranges) | np.isinf(ranges) | (ranges < data.range_min)] = 0
        ranges[ranges < data.range_min] = data.range_min
        ranges[(ranges > data.range_max) | (ranges > 6)] = 6

        padded = np.pad(ranges, (WINDOW_SIZE // 2,), mode="constant", constant_values=0)
        smoothed = np.convolve(padded, np.ones(WINDOW_SIZE), mode="valid") / WINDOW_SIZE

        angles = np.arange(data.angle_min, data.angle_max, data.angle_increment)
        min_idx = int(
            (math.radians(-ANGLE_LIMIT) - data.angle_min) / data.angle_increment
        )
        max_idx = int(
            (math.radians(ANGLE_LIMIT) - data.angle_min) / data.angle_increment
        )

        return smoothed[min_idx:max_idx], angles[min_idx:max_idx]

    def find_max_gap(self, free_space):
        start, max_len, curr_len, curr_start = 0, 0, 0, 0
        for i, r in enumerate(free_space):
            if r > RANGE_THRESHOLD:
                if curr_len == 0:
                    curr_start = i
                curr_len += 1
            else:
                if curr_len > max_len:
                    start, max_len = curr_start, curr_len
                curr_len = 0
        if curr_len > max_len:
            start, max_len = curr_start, curr_len
        return start, start + max_len - 1

    def find_best_point(self, start, end, angles):
        if end <= start:
            return start
        gap_indices = np.arange(start, end + 1)
        gap_angles = angles[gap_indices]
        angle_diffs = np.abs(gap_angles - self.user_heading_angle)
        best_idx_in_gap = gap_indices[np.argmin(angle_diffs)]
        return best_idx_in_gap

    def lidar_callback(self, data):
        proc_ranges, angles = self.preprocess_lidar(data)
        if proc_ranges is None or angles is None:
            return

        # Obstacle bubble masking
        closest_idx = np.argmin(proc_ranges)
        bubble_min = max(closest_idx - BUBBLE_RADIUS, 0)
        bubble_max = min(closest_idx + BUBBLE_RADIUS + 1, len(proc_ranges))
        proc_ranges[bubble_min:bubble_max] = 0

        start, end = self.find_max_gap(proc_ranges)
        if start == 0 and end == 0:
            # No valid gap found - stop and rotate to find space
            cmd = Twist()
            cmd.linear.x = 0.0
            cmd.angular.z = 0.3  # Slow rotation to find gap
            self.get_logger().warn("No valid gap found - rotating to search")
            self.drive_pub.publish(cmd)
            return

        best_idx = self.find_best_point(start, end, angles)
        steer_angle = angles[best_idx]

        velocity = 0.05  # Default minimum velocity for sharp turns
        for angle_deg, vel in VELOCITY_LIMITS:
            if abs(math.degrees(steer_angle)) <= angle_deg:
                velocity = vel
                break

        cmd = Twist()
        cmd.linear.x = velocity
        cmd.angular.z = -steer_angle
        self.get_logger().info(
            f"Steering: {math.degrees(steer_angle):.1f}°, Speed: {velocity:.2f}"
        )
        self.drive_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = ReactiveFollowGap()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
