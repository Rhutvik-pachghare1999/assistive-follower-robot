from setuptools import find_packages, setup

package_name = "my_nodes"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/my_nodes/launch", ["launch/planner_only.launch.py"]),
        (f"share/{package_name}", ["my_nodes/shoe_model.pth"]),
    ],
    install_requires=[
        "setuptools",
        "torch>=2.0",
        "torchvision>=0.15",
        "depthai>=2.21",
        "opencv-python>=4.5",
        "numpy>=1.22",
        "rclpy",
        "std_msgs",
        "ament_index_python",
    ],
    zip_safe=True,
    maintainer="Rhutvik Pachghare",
    maintainer_email="rpachgha@asu.edu",
    description="Assistive Follower Robot ROS 2 Package",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "gap_finder = my_nodes.scripts.gap_finder:main",
            "predict_publisher_node = my_nodes.scripts.predict_publisher_node:main",
            "gui = gui.ros2_gui:main",
        ],
    },
)
