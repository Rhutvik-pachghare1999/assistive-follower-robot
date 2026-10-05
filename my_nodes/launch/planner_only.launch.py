from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            namespace='/rpi_11',
            parameters=[
                {'use_sim_time': False},
                '/opt/ros/humble/share/turtlebot4_navigation/config/nav2.yaml'  # replace with actual path
            ],
            output='screen'
        )
    ])
