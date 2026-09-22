from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'my_robot_co2map'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.*')),
        
    ],
    
    install_requires=['setuptools','rclpy','pillow','pyyaml','tf-transformations'],
    
    zip_safe=True,
    maintainer='root',    
        entry_points={
            'console_scripts': [
                'trajectory_sender = my_robot_co2map.trajectory_sender:main',
                'trajectory_executor = my_robot_co2map.trajectory_executor:main',
                'trajectory_generator = my_robot_co2map.trajectory_generator:main',
                                ],
                    }
)