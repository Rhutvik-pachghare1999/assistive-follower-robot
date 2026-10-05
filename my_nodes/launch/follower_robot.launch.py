"""Launch file for the complete follower robot stack."""
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time if true'
        ),
        
        # Shoe detection node
        Node(
            package='my_nodes',
            executable='predict_publisher_node',
            name='predict_publisher_node',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
            remappings=[
                ('/color/preview/image', '/oakd/rgb/preview/image'),
            ]
        ),
        
        # Gap follower node
        Node(
            package='my_nodes',
            executable='gap_finder',
            name='gap_finder',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
            remappings=[
                ('/rpi_11/scan', '/scan'),
                ('/rpi_11/cmd_vel', '/cmd_vel'),
            ]
        ),
        
        # Optional: GUI for debugging
        # Node(
        #     package='my_nodes',
        #     executable='gui',
        #     name='ros2_gui',
        #     output='screen',
        # ),
    ])
