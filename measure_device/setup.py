from glob import glob
from setuptools import find_packages, setup

package_name = 'measure_device'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools', 'pyserial'],
    zip_safe=False,
    maintainer='Oleksii Vyshnevskyi',
    maintainer_email='lex.vyshnevskyy@gmail.com',
    description='ROS 2 publisher node for the E7-20 measurement device over RS232.',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'measure_device_node = measure_device.node:main',
        ],
    },
)
